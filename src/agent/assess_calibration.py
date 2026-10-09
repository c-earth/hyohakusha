"""Assess saved native-unit calibration without contacting the rover.

CLI input: run log directory containing trials.json/events.jsonl. Outputs:
report.md and measurements.json under the matching session analysis timestamp.
Pixel displacement and late-frame stability do not measure physical stop latency.
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


class CalibrationAssessment:
    """Compute image correspondence and stopped sensor summaries.

Constructor input is an existing run-log Path. Attributes hold capture/output
paths and a SIFT detector. Outputs are native-unit JSON and Markdown assessments.
"""

    def __init__(self, logs):
        """Locate run paths and initialize detector; returns None."""
        self.logs = logs.resolve()
        self.session = self.logs.parent.parent
        self.captures = self.session / 'captures' / self.logs.name
        self.output = self.session / 'analysis' / self.logs.name
        self.detector = cv2.SIFT_create(nfeatures=1800)

    def pair(self, first, second):
        """Return mutual SIFT median dx/dy/magnitude in px for two file names.

        Inputs are capture-relative strings. Output dictionary includes matches
        and homography inliers; inadequate support gives null pixel statistics.
        Correspondence is image evidence, not a physical pose estimate.
        """
        images = [cv2.imread(str(self.captures / name), cv2.IMREAD_GRAYSCALE) for name in (first, second)]
        if any(image is None for image in images) or images[0].shape != images[1].shape:
            raise ValueError('Unreadable/incompatible frames')
        keys, descriptors = zip(*(self.detector.detectAndCompute(image, None) for image in images))
        result = dict(first=first, second=second, matches=0, inliers=0, dx_px=None, dy_px=None, median_motion_px=None)
        if any(desc is None or len(desc) < 2 for desc in descriptors):
            return result
        matcher = cv2.BFMatcher()
        maps = []
        for a, b in ((0, 1), (1, 0)):
            maps.append({m.queryIdx: m.trainIdx for neighbors in matcher.knnMatch(descriptors[a], descriptors[b], k=2)
                         if len(neighbors) == 2 for m, n in [neighbors] if m.distance < 0.75*n.distance})
        pairs = [(a, b) for a, b in maps[0].items() if maps[1].get(b) == a]
        result['matches'] = len(pairs)
        if len(pairs) < 8:
            return result
        p, q = [np.float32([keys[index][pair[index]].pt for pair in pairs]) for index in (0, 1)]
        cv2.setRNGSeed(0)
        homography, mask = cv2.findHomography(p, q, cv2.RANSAC, 3)
        if homography is None or mask is None:
            return result
        accepted = mask.ravel().astype(bool)
        result['inliers'] = int(accepted.sum())
        if result['inliers'] < 8:
            return result
        delta = (q-p)[accepted]
        result.update(dx_px=float(np.median(delta[:, 0])), dy_px=float(np.median(delta[:, 1])),
                      median_motion_px=float(np.median(np.linalg.norm(delta, axis=1))))
        return result

    def run(self):
        """Read logs, assess trial/pan pairs and write report/JSON; returns None."""
        trials = json.loads((self.logs / 'trials.json').read_text())
        events = [json.loads(line) for line in (self.logs / 'events.jsonl').read_text().splitlines()]
        complete = next((event['payload'] for event in events if event['kind'] == 'complete'), None)
        baseline = complete['baseline'] if complete else next((event['payload']['samples'] for event in events if event['kind'] == 'baseline'), [])
        gyro_noise = np.std(np.asarray([sample['gyro'] for sample in baseline]), axis=0) if baseline else np.zeros(3)
        frames = json.loads((self.captures / 'frames.json').read_text())
        measured = []
        for trial in trials:
            telemetry = [sample for sample in trial.get('gyro_telemetry', []) if sample.get('sensor', 'gyro') == 'gyro']
            accel = [sample for sample in trial.get('gyro_telemetry', []) if sample.get('sensor') == 'accel']
            accel_peak = float(np.max(np.linalg.norm(np.asarray([sample['xyz'] for sample in accel])-np.asarray(trial['before']['accel']), axis=1))) if accel else None
            settling = None
            peak_z = None
            integral_z = None
            if telemetry:
                raw = np.asarray([sample['xyz'] for sample in telemetry], dtype=float)
                delta = raw - np.asarray(trial['before']['gyro'])
                times = np.asarray([sample['received_ms'] for sample in telemetry])
                integral_z = float(np.trapezoid(delta[:, 2], times/1000))
                inside = np.all(np.abs(delta) <= np.maximum(5*gyro_noise, 50), axis=1)
                peak_index = np.argmax(np.abs(delta[:, 2]))
                peak_z = float(delta[peak_index, 2])
                for index in range(len(times)):
                    if times[index] >= trial['host_stop_elapsed_ms'] and times[-1]-times[index] >= 200 and np.all(inside[index:]):
                        settling = float(times[index]-trial['host_stop_elapsed_ms'])
                        break
            measured.append(dict(direction=trial['direction'], repeat=trial['repeat'], early_stop=trial['early_stop'],
                                 stop_sent_ms=trial['host_stop_elapsed_ms'],
                                 gyro_samples=len(telemetry), peak_bias_relative_z_counts=peak_z,
                                 gyro_z_receipt_integral_count_seconds=integral_z,
                                 accel_samples=len(accel), peak_accel_residual_counts=accel_peak,
                                 gyro_return_after_host_stop_ms=settling,
                                 motion=self.pair(trial['first'], trial['second']),
                                 late_stability=self.pair(trial['second'], trial['later'])))
        pan = [frame['file'] for frame in frames if '-pan-' in frame['file'] or '-step-' in frame['file']]
        pan_pairs = [self.pair(a, b) for a, b in zip(pan, pan[1:])]
        summary = {}
        for name in ('battery_v', 'echo_us', 'gyro', 'accel', 'floor'):
            if baseline:
                values = np.asarray([sample[name] for sample in baseline], dtype=float)
                summary[name] = dict(mean=np.mean(values, axis=0).tolist(), std=np.std(values, axis=0).tolist(),
                                     minimum=np.min(values, axis=0).tolist(), maximum=np.max(values, axis=0).tolist())
        self.output.mkdir(parents=True, exist_ok=False)
        result = dict(run_complete=complete is not None, baseline=summary, trials=measured, pan_pairs=pan_pairs)
        (self.output / 'measurements.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        lines = ['# Native-unit calibration assessment', '',
                 f'Completed control sequence: {complete is not None}. Recorded drive trials: {len(trials)}.',
                 f"Safe calibration area is a user assumption. PWM={trials[0]['pwm'] if trials else 'unknown'}; firmware T={trials[0]['duration_ms'] if trials else 'unknown'} ms; early N100 at half duration.", '',
                 '| Direction | Stop mode | Repeats | Median motion px | Median late-frame motion px |',
                 '|---|---|---:|---:|---:|']
        for direction in ('forward', 'backward', 'left', 'right'):
            for early in (False, True):
                group = [item for item in measured if item['direction'] == direction and item['early_stop'] == early]
                motion = [item['motion']['median_motion_px'] for item in group if item['motion']['median_motion_px'] is not None]
                late = [item['late_stability']['median_motion_px'] for item in group if item['late_stability']['median_motion_px'] is not None]
                motion_text = f'{np.median(motion):.3f}' if motion else 'unknown'
                late_text = f'{np.median(late):.3f}' if late else 'unknown'
                lines.append(f"| {direction} | {'early N100' if early else 'expiry then N100'} | {len(group)} | {motion_text} | {late_text} |")
        lines += ['', '| Direction | Stop mode | Median peak bias-relative gyro Z counts | Median gyro return after host stop ms |',
                  '|---|---|---:|---:|']
        for direction in ('forward', 'backward', 'left', 'right'):
            for early in (False, True):
                group = [item for item in measured if item['direction'] == direction and item['early_stop'] == early]
                peak = [item['peak_bias_relative_z_counts'] for item in group if item['peak_bias_relative_z_counts'] is not None]
                settle = [item['gyro_return_after_host_stop_ms'] for item in group if item['gyro_return_after_host_stop_ms'] is not None]
                peak_text = f'{np.median(peak):.1f}' if peak else 'unmeasured'
                settle_text = f'{np.median(settle):.1f} ({len(settle)}/{len(group)} trials)' if settle else 'unestablished'
                lines.append(f"| {direction} | {'early N100' if early else 'expiry then N100'} | {peak_text} | {settle_text} |")
        lines += ['', '## Limits and remaining work', '',
                  'Gyro Z residual integral is saved in count-seconds using host receipt times; it is not calibrated yaw.',
                  'Accelerometer residual peaks are saved in raw counts. Gravity, vibration and bias prevent reliable position integration.',
                  'Before/after images support image response; low late-frame displacement supports later image stability only.',
                  'Gyro return uses all-axis residual <= max(5 baseline standard deviations, 50 counts), sustained to the end for >=200 ms.',
                  'Times are host receipt times relative to N100 send; sensor acquisition/network latency are unknown.',
                  'A returned gyro indicates low angular response, not absence of translation. Gyro sampling can perturb serial/expiry timing.',
                  'There is no continuous motion image record, measured physical stopping distance, physical scale, calibrated yaw,',
                  'held-out predictive validation, disconnect fault trial or exploration clearance controller. Calibration remains partial.',
                  'A 100 ms pulse can be below motor response onset; no-response trials are not proof of calibrated velocity.',
                  'N5/N6 image pairs and raw baseline summaries are in measurements.json. Actual servo angle is unmeasured.',
                  'Only the PWM/duration conditions in trials.json were tested. This report does not establish readiness for autonomous exploration.']
        (self.output / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(self.output / 'report.md')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('logs', type=Path)
    CalibrationAssessment(parser.parse_args().logs).run()
