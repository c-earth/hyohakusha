"""Assess saved motion evidence, retaining unsupported and failed trials.

CLI inputs: run log directory and new output directory. Emits JSON and Markdown
with full-gyro nominal Z integration, rest support and held-out consistency.
No hardware contact, absolute heading or metric pose is inferred.
"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from src.agent.runtime.gyro_bias import GyroBiasCalibrator

from .assess_calibration import CalibrationAssessment
from .inertial import InertialIntegrator


class MotionValidation:
    """Assess one acquisition with explicit evidence exclusions and provenance.

    logs/output are Paths. Captures are resolved from the historical session
    layout; numerical/image diagnostics do not open a control connection.
    """

    def __init__(self, logs, output):
        """Locate captures and initialize image and inertial diagnostics."""
        self.logs, self.output = logs, output
        self.captures = logs.parent.parent/'captures'/logs.name
        self.images = CalibrationAssessment(logs)
        self.integrator = InertialIntegrator()

    def rest_evidence(self, frames, samples, begin, end, bias):
        """Return provisional rest support wholly inside a seconds time window.

        frames have capture-relative filenames and host request/receipt ms;
        samples contain raw gyro/accel vectors. Require two images and three
        observations of each sensor; compare gyro mean to stopped bias.
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
        result.update(accepted=bool(accepted), image_motion=flow,
                      gyro_std=gyro_std.tolist(), accel_std=accel_std.tolist())
        if not accepted:
            result['reason'] = 'Image/IMU rest thresholds rejected'
        return result

    def assess_trial(self, index, trial):
        """Return a retained trial result with explicit reasons for exclusion.

        Trial dictionaries may use the old complete-only schema or new status/
        motion fields. Gyro-only turn estimates use full supported gyro time;
        acceleration-dependent diagnostics retain their shorter overlap.
        """
        samples = trial.get('gyro_telemetry', [])
        result = dict(index=index, repeat=trial.get('repeat'), direction=trial.get('direction'),
                      early_stop=trial.get('early_stop'), status=trial.get('status', 'complete'),
                      frames=len(trial.get('timed_frames', [])), gyro_samples=0, accel_samples=0,
                      gyro_z_integral_deg_nominal=None, median_gyro_gap_ms=None,
                      active_gyro_median_gap_ms=None, pre_rest=dict(accepted=False),
                      post_rest=dict(accepted=False), eligible=False, exclusion_reasons=[])
        reasons = result['exclusion_reasons']
        if result['status'] != 'complete':
            reasons.append('Incomplete trial: '+trial.get('error', 'acquisition did not finish'))
        try:
            gt, gr = self.integrator.series(samples, 'gyro', 'midpoint')
            at, ar = self.integrator.series(samples, 'accel', 'midpoint')
            result.update(gyro_samples=len(gt), accel_samples=len(at))
            bias = trial['gyro_bias']
            gyro_trace = self.integrator.yaw_trace(gt, gr, bias['bias_raw_xyz'])
            result['gyro_z_integral_deg_nominal'] = gyro_trace['gyro_z_integral_deg_nominal'][-1]
            result['gyro_support_s'] = [float(gt[0]), float(gt[-1])]
            result['median_gyro_gap_ms'] = float(np.median(np.diff(gt))*1000)
            (self.output/f'trial-{index:03d}-gyro.json').write_text(json.dumps(gyro_trace, indent=2), encoding='utf-8')
            motion = trial.get('motion', {})
            drive_s = (motion.get('drive_send_ms') or 0)/1000
            stop_s = trial['host_stop_elapsed_ms']/1000
            active_gt = gt[(gt >= drive_s-0.1) & (gt <= stop_s+0.3)]
            result['active_gyro_median_gap_ms'] = float(np.median(np.diff(active_gt))*1000) if len(active_gt) > 1 else None
            result['command_timing'] = dict(drive_send_ms=motion.get('drive_send_ms'),
                                            stop_elapsed_ms=trial['host_stop_elapsed_ms'],
                                            drive_send_bracket_ns=motion.get('drive_send_bracket_ns'),
                                            stop_send_bracket_ns=motion.get('stop_send_bracket_ns'))
            frames = trial.get('timed_frames', [])
            if frames and trial.get('timed_folder'):
                timed = [dict(frame, file=trial['timed_folder']+'/'+frame['file']) for frame in frames]
                result['pre_rest'] = self.rest_evidence(timed, samples, -1.1, drive_s, bias)
                result['post_rest'] = self.rest_evidence(timed, samples, stop_s+0.6,
                                                        max(frame['received_ms']/1000 for frame in timed), bias)
            else:
                reasons.append('Missing timed camera evidence')
            if trial.get('first') and trial.get('second'):
                result['visual'] = self.images.pair(trial['first'], trial['second'])
            else:
                reasons.append('Missing before/after image pair')
            if len(at) >= 2:
                trace = self.integrator.integrate(gt, gr, at, ar, bias['bias_raw_xyz'], bias['accel_reference_raw_xyz'])
                result['overlap_yaw_deg_nominal'] = trace['yaw_deg_nominal'][-1]
                velocity = np.asarray(trace['velocity_increment_m_s_nominal'])
                result['residual_velocity_m_s_nominal'] = float(np.linalg.norm(velocity[-1]))
                if result['pre_rest']['accepted'] and result['post_rest']['accepted']:
                    times = np.asarray(trace['time_s'])
                    acceleration = np.asarray(trace['acceleration_initial_frame_m_s2_nominal'])
                    correction = velocity[-1]/(times[-1]-times[0])
                    corrected_v, corrected_p = self.integrator.cumulative(times, acceleration-correction)
                    result['rest_constrained'] = dict(assumption='zero velocity at both observed endpoints',
                                                     final_velocity_m_s=corrected_v[-1].tolist(),
                                                     displacement_m_conditional=corrected_p[-1].tolist(),
                                                     validated_distance=False)
                (self.output/f'trial-{index:03d}-trace.json').write_text(json.dumps(trace, indent=2), encoding='utf-8')
        except (KeyError, ValueError, TypeError, OSError) as error:
            reasons.append('Unsupported evidence: '+str(error))
        for label in ('pre_rest', 'post_rest'):
            if not result[label]['accepted']:
                reasons.append(label+': '+result[label].get('reason', 'missing support'))
        if result.get('visual', {}).get('dx_px') is None:
            reasons.append('No supported visual displacement')
        result['eligible'] = not reasons
        return result

    @staticmethod
    def compare_turns(results):
        """Fit eligible repeat-0 turns and check eligible later repeats only.

        Results carry nominal sensor-Z angle and visual dx in pixels. Keep the
        original >=2-degree training support gate. Return ratio, fitted indices,
        and held-out checks; a fit to nominal gyro angle is not absolute truth.
        """
        training = [item for item in results if item['eligible'] and item['repeat'] == 0
                    and item['direction'] in ('left', 'right')
                    and abs(item['gyro_z_integral_deg_nominal']) >= 2]
        ratio = float(np.median([item['visual']['dx_px']/item['gyro_z_integral_deg_nominal'] for item in training])) if training else None
        checks = []
        if ratio is not None and np.isfinite(ratio) and abs(ratio) > 0.1:
            for item in results:
                if item['eligible'] and item['repeat'] > 0 and item['direction'] in ('left', 'right'):
                    estimate = item['visual']['dx_px']/ratio
                    checks.append(dict(index=item['index'], gyro_yaw_deg_nominal=item['gyro_z_integral_deg_nominal'],
                                       vision_yaw_deg_from_training=estimate,
                                       difference_deg=estimate-item['gyro_z_integral_deg_nominal']))
        return ratio, [item['index'] for item in training], checks

    def run(self):
        """Save diagnostics and a report with acquisition/cleanup completeness."""
        self.output.mkdir(parents=True, exist_ok=False)
        trials_path, events_path = self.logs/'trials.json', self.logs/'events.jsonl'
        trials = json.loads(trials_path.read_text(encoding='utf-8'))
        events, event_errors = [], []
        try:
            for number, line in enumerate(events_path.read_text(encoding='utf-8').splitlines(), start=1):
                try:
                    events.append(json.loads(line))
                except ValueError:
                    event_errors.append(f'Unreadable event line {number}')
        except OSError as error:
            event_errors.append(str(error))
        results = [self.assess_trial(index, trial) for index, trial in enumerate(trials)]
        ratio, fitted, checks = self.compare_turns(results)
        failures = [event.get('payload', {}) for event in events if event.get('kind') in ('failure', 'cleanup_failure')]
        cleanup_recorded = any(event.get('kind') == 'cleanup'
                               and event.get('payload', {}).get('socket_closed')
                               and event.get('payload', {}).get('stop_error') is None for event in events)
        acquisition_complete = any(event.get('kind') == 'complete' for event in events) and cleanup_recorded and not failures and not event_errors
        summary = dict(schema_version=2, source=str(self.logs.resolve()),
                       trials_sha256=hashlib.sha256(trials_path.read_bytes()).hexdigest(),
                       events_sha256=hashlib.sha256(events_path.read_bytes()).hexdigest() if events_path.exists() else None,
                       acquisition_complete=acquisition_complete, acquisition_failures=failures,
                       cleanup_recorded=cleanup_recorded,
                       event_errors=event_errors, nominal_scales_unverified=True,
                       heading_method='full-support bias-corrected sensor-Z trapezoid; no deadband',
                       training_pixel_per_nominal_deg=ratio, fitted_trials=fitted,
                       held_out=checks, trials=results, metric_pose_validated=False)
        (self.output/'validation.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        differences = [abs(item['difference_deg']) for item in checks]
        lines = ['# Motion observation validation', '',
                 f'Acquisition complete without logged cleanup failures: {acquisition_complete}.',
                 f'Positive stop-attempt/socket-close record: {cleanup_recorded} (older runs may lack this event).',
                 f'Recorded trials: {len(results)}; eligible for consistency analysis: {sum(item["eligible"] for item in results)}.',
                 'Heading uses full-gyro sensor Z; previous reports used accel-overlap Euler yaw. Do not compare their medians as an unchanged method.',
                 f'Pixel/nominal-degree fit from eligible first-repeat turns: {ratio}.',
                 f'Held-out turn checks: {len(checks)}; median absolute difference: {float(np.median(differences)) if differences else None} nominal degrees.',
                 f'Logged acquisition/cleanup failures: {failures}; event read errors: {event_errors}.', '',
                 '| Trial | Direction | Status | Nominal Z angle | Pre/post rest | Exclusion reasons |',
                 '|---:|---|---|---:|---|---|']
        for item in results:
            reason = '; '.join(item['exclusion_reasons']).replace('|', '/')
            lines.append(f'| {item["index"]} | {item["direction"]} | {item["status"]} | {item["gyro_z_integral_deg_nominal"]} | {item["pre_rest"]["accepted"]}/{item["post_rest"]["accepted"]} | {reason} |')
        lines += ['', 'Host request/receipt/send brackets are not device acquisition or execution timestamps.',
                  'Rest support and image/gyro consistency do not establish absolute heading, metric distance or physical stopping clearance.',
                  'Rest-constrained endpoints are imposed diagnostics. Failed/incomplete evidence is retained and excluded from fitting.']
        (self.output/'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        print(self.output/'report.md')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('logs', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    MotionValidation(args.logs, args.output).run()
