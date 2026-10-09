"""Validate timed vision/IMU observations offline without contacting hardware.

CLI inputs: calibration log Path and new output Path. Outputs JSON/report of
image settling, nominal gyro integration and held-out visual/gyro consistency.
Metric scale and physical stopping distance are not inferred.
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

from assess_calibration import CalibrationAssessment
from gyro_bias import GyroBiasCalibrator
from integrate_imu import InertialIntegrator, IntegrationAssessment


class MotionValidation:
    """Assess time-aligned camera/IMU trials with rest and held-out checks.

Constructor inputs are log/output Paths. Uses source-based nominal scales and
each trial's stopped bias. No hardware actions; output is diagnostic evidence.
"""

    def __init__(self, logs, output):
        """Locate captures and initialize numerical/image tools; return None."""
        self.logs, self.output = logs, output
        self.captures = logs.parent.parent/'captures'/logs.name
        self.images = CalibrationAssessment(logs)
        self.integrator = InertialIntegrator()

    def rest_evidence(self, frames, samples, begin, end, bias):
        """Return rest-support dictionary for time window in seconds.

        Inputs: relative frame names/host times, IMU samples, begin/end seconds
        and bias metadata. Requires camera interval wholly within window plus
        >=3 gyro and accel samples. Provisional raw noise bands and optical flow
        support rest but do not prove physical zero velocity.
        """
        views = [frame for frame in frames if frame['request_ms']/1000 >= begin and frame['received_ms']/1000 <= end]
        gyro = [sample['xyz'] for sample in samples if sample['sensor'] == 'gyro' and begin <= sample['request_ms']/1000 <= sample['received_ms']/1000 <= end]
        accel = [sample['xyz'] for sample in samples if sample['sensor'] == 'accel' and begin <= sample['request_ms']/1000 <= sample['received_ms']/1000 <= end]
        result = dict(accepted=False, views=len(views), gyro_samples=len(gyro), accel_samples=len(accel))
        if len(views) < 2 or len(gyro) < 3 or len(accel) < 3:
            result['reason'] = 'Insufficient bounded-time rest observations'
            return result
        first, second = [cv2.imread(str(self.captures/frame['file'])) for frame in (views[0], views[-1])]
        try:
            flow = GyroBiasCalibrator.image_motion(first, second)
        except ValueError as error:
            result['reason'] = str(error)
            return result
        gyro_mean = np.mean(gyro, axis=0)
        gyro_std, accel_std = np.std(gyro, axis=0), np.std(accel, axis=0)
        accepted = flow['median_px'] <= 1 and flow['p95_px'] <= 3 and np.all(np.abs(gyro_mean-bias['bias_raw_xyz']) <= 70) and np.all(gyro_std <= 50) and np.all(accel_std <= 300)
        result.update(accepted=bool(accepted), image_motion=flow, gyro_std=gyro_std.tolist(), accel_std=accel_std.tolist())
        return result

    def run(self):
        """Validate saved trials, fit repeat 0/test later repeats; save JSON/report."""
        self.output.mkdir(parents=True, exist_ok=False)
        trials = json.loads((self.logs/'trials.json').read_text())
        results = []
        for index, trial in enumerate(trials):
            samples = trial['gyro_telemetry']
            gt, gr = IntegrationAssessment.series(samples, 'gyro', 'midpoint')
            at, ar = IntegrationAssessment.series(samples, 'accel', 'midpoint')
            bias = trial['gyro_bias']
            trace = self.integrator.integrate(gt, gr, at, ar, bias['bias_raw_xyz'], bias['accel_reference_raw_xyz'])
            timed = [dict(frame, file=trial['timed_folder']+'/'+frame['file']) for frame in trial['timed_frames']]
            pairs = []
            for first, second in zip(timed, timed[1:]):
                value = self.images.pair(first['file'], second['file'])
                value.update(request_ms=second['request_ms'], received_ms=second['received_ms'])
                pairs.append(value)
            stop_s = trial['host_stop_elapsed_ms']/1000
            begin, end = trace['time_s'][0], trace['time_s'][-1]
            pre = self.rest_evidence(timed, samples, -1.1, 0, bias)
            post = self.rest_evidence(timed, samples, stop_s+0.6, max(frame['received_ms']/1000 for frame in timed), bias)
            velocity = np.asarray(trace['velocity_increment_m_s_nominal'])
            active_gt = gt[(gt >= -0.1) & (gt <= stop_s+0.3)]
            result = dict(index=index, repeat=trial['repeat'], direction=trial['direction'], early_stop=trial['early_stop'],
                          yaw_deg_nominal=trace['yaw_deg_nominal'][-1], visual=self.images.pair(trial['first'], trial['second']),
                          gyro_samples=len(gt), accel_samples=len(at), frames=len(timed),
                          median_gyro_gap_ms=float(np.median(np.diff(gt))*1000),
                          median_accel_gap_ms=float(np.median(np.diff(at))*1000),
                          active_gyro_samples=len(active_gt), active_gyro_median_gap_ms=float(np.median(np.diff(active_gt))*1000) if len(active_gt) > 1 else None,
                          pre_rest=pre, post_rest=post, timed_image_pairs=pairs,
                          residual_velocity_m_s_nominal=float(np.linalg.norm(velocity[-1])))
            if pre['accepted'] and post['accepted']:
                # Explicit endpoint constraint; preserve unconstrained estimate too.
                times = np.asarray(trace['time_s'])
                acceleration = np.asarray(trace['acceleration_initial_frame_m_s2_nominal'])
                correction = velocity[-1]/(end-begin)
                corrected_v, corrected_p = self.integrator.cumulative(times, acceleration-correction)
                result['rest_constrained'] = dict(assumption='zero velocity at both observed endpoints',
                                                 constant_accel_correction_m_s2=correction.tolist(),
                                                 final_velocity_m_s=corrected_v[-1].tolist(),
                                                 displacement_m_conditional=corrected_p[-1].tolist(),
                                                 validated_distance=False)
            (self.output/f'trial-{index:03d}-trace.json').write_text(json.dumps(trace, indent=2), encoding='utf-8')
            results.append(result)
        training = [item for item in results if item['repeat'] == 0 and item['direction'] in ('left', 'right') and abs(item['yaw_deg_nominal']) >= 2 and item['visual']['dx_px'] is not None]
        ratio = float(np.median([item['visual']['dx_px']/item['yaw_deg_nominal'] for item in training])) if training else None
        checks = []
        if ratio is not None and abs(ratio) > 0.1:
            for item in results:
                if item['repeat'] > 0 and item['direction'] in ('left', 'right') and item['visual']['dx_px'] is not None:
                    estimate = item['visual']['dx_px']/ratio
                    checks.append(dict(index=item['index'], gyro_yaw_deg_nominal=item['yaw_deg_nominal'],
                                       vision_yaw_deg_from_training=estimate, difference_deg=estimate-item['yaw_deg_nominal']))
        summary = dict(source=str(self.logs.resolve()), nominal_scales_unverified=True, training_pixel_per_nominal_deg=ratio,
                       held_out=checks, trials=results, metric_pose_validated=False)
        (self.output/'validation.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        lines = ['# Motion observation validation', '', f'Trials: {len(results)}. Camera and IMU brackets share host monotonic time.',
                 f'Pre-motion rest supported: {sum(item["pre_rest"]["accepted"] for item in results)}.',
                 f'Post-motion rest supported: {sum(item["post_rest"]["accepted"] for item in results)}.',
                 f'Rest-constrained displacement scenarios: {sum("rest_constrained" in item for item in results)} (conditional, not validated distance).',
                 f'Pixel/nominal-degree fit from first repeat: {ratio}.',
                 f'Held-out turn checks: {len(checks)}.',
                 f'Median held-out absolute difference: {np.median([abs(item["difference_deg"]) for item in checks]) if checks else None} nominal degrees.', '',
                 '| Trial | Direction | Early stop | Nominal yaw deg | Timed frames | Gyro gap ms | Accel gap ms | Pre/post rest |',
                 '|---:|---|---|---:|---:|---:|---:|---|']
        for item in results:
            lines.append(f'| {item["index"]} | {item["direction"]} | {item["early_stop"]} | {item["yaw_deg_nominal"]:.3f} | {item["frames"]} | {item["median_gyro_gap_ms"]:.1f} | {item["median_accel_gap_ms"]:.1f} | {item["pre_rest"]["accepted"]}/{item["post_rest"]["accepted"]} |')
        lines += ['', 'Camera host brackets are not exposure timestamps; IMU acquisition timestamps and installed scale checks remain absent.',
                  'Image/gyro agreement checks consistency within this scene, not absolute angular accuracy.',
                  'A rest-constrained velocity endpoint is imposed, not an independently measured successful velocity estimate.',
                  'Rest failures stay uncorrected. Floor/ultrasound values remain supporting raw evidence; no cliff/obstacle clearance guarantee.',
                  'Camera intrinsics, metric travel and physical stop distance remain uncalibrated.']
        (self.output/'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        print(self.output/'report.md')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('logs', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    MotionValidation(args.logs, args.output).run()
