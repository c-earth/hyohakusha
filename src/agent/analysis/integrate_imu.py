"""Integrate saved gyro and accelerometer observations offline.

CLI inputs are one or more calibration log directories and a new output path.
Outputs: numerical traces, timing/bias sensitivity results and report. No rover
contact. Nominal units assume source-configured 131 counts/(deg/s), 16384 counts/g
and standard gravity 9.80665 m/s²; device configuration/scales remain unverified.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from .inertial import InertialIntegrator


class IntegrationAssessment:
    """Assess saved trial integration and its timing/bias sensitivity.

Constructor inputs: log-directory Paths and new output Path. Saves per-trial
traces and summary under output; never opens a rover connection. Source run
paths/hashes and nominal-unit assumptions accompany all estimates.
"""

    def __init__(self, logs, output):
        """Store input/output Paths and initialize integrator; no outputs yet."""
        self.logs = logs
        self.output = output
        self.integrator = InertialIntegrator()

    def run(self):
        """Integrate all supported trials and save JSON/CSV/report; returns None."""
        self.output.mkdir(parents=True, exist_ok=False)
        results, provenance = [], []
        for log in self.logs:
            trials_path = log / 'trials.json'
            events = [json.loads(line) for line in (log / 'events.jsonl').read_text().splitlines()]
            baseline = next((event['payload']['samples'] for event in events if event['kind'] == 'baseline'), None)
            if baseline is None:
                baseline = next((event['payload']['baseline'] for event in events if event['kind'] == 'complete'), [])
            provenance.append(dict(path=str(log.resolve()), trials_sha256=hashlib.sha256(trials_path.read_bytes()).hexdigest(),
                                   events_sha256=hashlib.sha256((log/'events.jsonl').read_bytes()).hexdigest()))
            for index, trial in enumerate(json.loads(trials_path.read_text())):
                samples = trial.get('gyro_telemetry', [])
                result = dict(run=log.name, index=index, direction=trial['direction'], early_stop=trial['early_stop'],
                              pwm=trial['pwm'], duration_ms=trial['duration_ms'],
                              host_stop_s=trial.get('host_stop_elapsed_ms', 0)/1000, scenarios=[])
                if trial.get('status', 'complete') != 'complete':
                    result['unsupported'] = trial.get('error', 'Incomplete acquisition')
                    results.append(result)
                    continue
                if sum(sample.get('sensor') == 'accel' for sample in samples) < 2:
                    result['unsupported'] = 'Insufficient accelerometer samples'
                    results.append(result)
                    continue
                for clock in ('request', 'midpoint', 'receipt'):
                    gt, gr = InertialIntegrator.series(samples, 'gyro', clock)
                    at, ar = InertialIntegrator.series(samples, 'accel', clock)
                    for bias_name in ('trial_before', 'run_baseline'):
                        reference = dict(trial['before']) if bias_name == 'trial_before' else {
                            name: np.mean([item[name] for item in baseline], axis=0) for name in ('gyro', 'accel')}
                        if bias_name == 'trial_before' and 'gyro_bias' in trial:
                            reference['gyro'] = trial['gyro_bias']['bias_raw_xyz']
                            reference['accel'] = trial['gyro_bias']['accel_reference_raw_xyz']
                        trace = self.integrator.integrate(gt, gr, at, ar, reference['gyro'], reference['accel'])
                        summary = dict(clock=clock, bias= bias_name, start_s=trace['time_s'][0], end_s=trace['time_s'][-1],
                                       yaw_deg_nominal=trace['yaw_deg_nominal'][-1],
                                       velocity_increment_m_s_nominal=trace['velocity_increment_m_s_nominal'][-1],
                                       displacement_m_nominal=trace['displacement_m_nominal_zero_initial_velocity'][-1])
                        result['scenarios'].append(summary)
                        if clock == 'midpoint' and bias_name == 'trial_before':
                            filename = f'{log.name}-trial-{index:03d}.json'
                            (self.output/filename).write_text(json.dumps(trace, indent=2), encoding='utf-8')
                            result['trace'] = filename
                variants = result['scenarios']
                result['yaw_scenario_span_deg'] = float(np.ptp([item['yaw_deg_nominal'] for item in variants]))
                positions = np.asarray([item['displacement_m_nominal'] for item in variants])
                result['position_scenario_component_span_m'] = np.ptp(positions, axis=0).tolist()
                results.append(result)
        document = dict(assumptions=dict(gyro_counts_per_deg_s=131, accel_counts_per_g=16384, gravity_m_s2=9.80665,
                                        device_scale_verified=False, timestamps='host request/receipt hypotheses',
                                        initial_velocity='zero at common sample window start, not established during pulse',
                                        frame='initial sensor axes, not room coordinates', localization_validated=False),
                        provenance=provenance, trials=results)
        (self.output/'integration.json').write_text(json.dumps(document, indent=2), encoding='utf-8')
        self.report(results)
        self.plot(results)
        print(self.output/'report.md')

    def plot(self, results):
        """Save four-panel PNG for final-run forward/left expiry examples.

        Input is list of assessed trial dictionaries. Output is integration.png
        with assumed-scale yaw, acceleration, velocity increment and displacement
        traces. Returns None; no plot is created when no usable trace exists.
        """
        usable = [item for item in results if 'trace' in item]
        if not usable:
            return
        run = usable[-1]['run']
        selected = [next((item for item in usable if item['run'] == run and item['direction'] == direction and not item['early_stop']), None)
                    for direction in ('forward', 'left')]
        figure = Figure(figsize=(11, 7), dpi=140)
        FigureCanvasAgg(figure)
        axes = figure.subplots(2, 2).ravel()
        names = ('yaw_deg_nominal', 'acceleration_initial_frame_m_s2_nominal', 'velocity_increment_m_s_nominal', 'displacement_m_nominal_zero_initial_velocity')
        labels = ('Integrated yaw (nominal deg)', 'Acceleration residual norm (nominal m/s²)',
                  'Velocity increment norm (nominal m/s)', 'Displacement norm (conditional m)')
        for item, color in zip(selected, ('#1769aa', '#b35b00')):
            if item is None:
                continue
            trace = json.loads((self.output/item['trace']).read_text())
            for axis, name in zip(axes, names):
                values = np.asarray(trace[name])
                if values.ndim == 2:
                    values = np.linalg.norm(values, axis=1)
                axis.plot(trace['time_s'], values, color=color, label=f"{item['direction']}, PWM {item['pwm']}")
                axis.axvline(item['host_stop_s'], color=color, linestyle=':', alpha=0.7)
        for axis, label in zip(axes, labels):
            axis.set_xlabel('Time from logged motion epoch (s)')
            axis.set_ylabel(label)
            axis.grid(alpha=0.2)
            axis.legend(fontsize=8)
        figure.suptitle('Gyro and acceleration integration: assumed scales and timing\nDotted lines: host N100 send; curves begin at overlapping observed support')
        figure.tight_layout(rect=(0, 0, 1, 0.92))
        figure.savefig(self.output/'integration.png')

    def report(self, results):
        """Write grouped Markdown/CSV from result dictionaries; return None."""
        lines = ['# Gyro and acceleration time integration', '',
                 'Conditional estimates use source-configured nominal scales; installed register values/scale accuracy were not measured.',
                 'Gyro bias removed, orientation integrated; acceleration rotated into initial sensor axes and stationary reference subtracted.',
                 'Acceleration integrated once for velocity increment and twice for displacement with zero velocity at observed-window start.', '',
                 '| PWM | Direction | Stop | Trials | Median yaw deg (nominal) | Median displacement norm m (conditional) |',
                 '|---|---|---|---:|---:|---:|']
        rows = []
        for item in results:
            if 'unsupported' in item:
                continue
            primary = next(s for s in item['scenarios'] if s['clock'] == 'midpoint' and s['bias'] == 'trial_before')
            rows.append(dict(run=item['run'], trial=item['index'], pwm=item['pwm'], direction=item['direction'], early_stop=item['early_stop'],
                             yaw_deg_nominal=primary['yaw_deg_nominal'], displacement_norm_m_nominal=float(np.linalg.norm(primary['displacement_m_nominal'])),
                             final_velocity_increment_norm_m_s_nominal=float(np.linalg.norm(primary['velocity_increment_m_s_nominal'])),
                             yaw_scenario_span_deg=item['yaw_scenario_span_deg'], position_scenario_span_norm_m=float(np.linalg.norm(item['position_scenario_component_span_m']))))
        for pwm in sorted({row['pwm'] for row in rows}):
            for direction in ('forward', 'backward', 'left', 'right'):
                for early in (False, True):
                    group = [r for r in rows if r['pwm'] == pwm and r['direction'] == direction and r['early_stop'] == early]
                    if group:
                        lines.append(f"| {pwm} | {direction} | {'early' if early else 'expiry'} | {len(group)} | {np.median([r['yaw_deg_nominal'] for r in group]):.3f} | {np.median([r['displacement_norm_m_nominal'] for r in group]):.4f} |")
        if rows:
            with (self.output/'summary.csv').open('w', newline='', encoding='utf-8') as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            lines += ['', f"Median residual velocity increment norm: {np.median([r['final_velocity_increment_norm_m_s_nominal'] for r in rows]):.4f} m/s (conditional).",
                      f"Median yaw span over six timing/bias scenarios: {np.median([r['yaw_scenario_span_deg'] for r in rows]):.3f} deg.",
                      f"Median displacement component-span norm: {np.median([r['position_scenario_span_norm_m'] for r in rows]):.4f} m."]
        lines += ['', '## Interpretation limits', '',
                  'Residual velocity increments remain despite later stable images; acceleration integration has not established displacement.',
                  'These scenario spans are sensitivity tests, not uncertainty bounds or confidence intervals.',
                  'Alternating gyro/accel samples miss fast onset/braking; neither has sensor acquisition timestamps.',
                  'Only overlapping observed support is used; missed startup intervals and initial velocity are unknown.',
                  'Stationary acceleration contains gravity plus bias; separating them requires more calibration.',
                  'Turning rotates accelerometer bias too; the reference-vector subtraction assumes that effect is negligible.',
                  'No end-velocity constraint was imposed and no drift correction was used to force expected travel.',
                  'The result is an inertial integration diagnostic, not measured room coordinates or validated distance.',
                  'Source: rover/firmware/src/uno/MPU6050.cpp initialize() selects ±250 deg/s and ±2g.',
                  'Nominal sensitivities: [MPU-6050 register map](https://www.invensense.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf).']
        (self.output/'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('logs', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    IntegrationAssessment(args.logs, args.output).run()
