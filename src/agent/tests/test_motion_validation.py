"""Check evidence exclusions and incomplete-run reporting without hardware."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.agent.analysis.assess_calibration import CalibrationAssessment
from src.agent.analysis.integrate_imu import IntegrationAssessment
from src.agent.analysis.validate_motion import MotionValidation


class MotionValidationTests(unittest.TestCase):
    """Use synthetic result records and isolated output directories."""

    def test_rejected_rest_cannot_fit_or_validate(self):
        """An ineligible outlier cannot alter the fit or held-out checks."""
        results = [
            dict(index=0, eligible=True, repeat=0, direction='left',
                 gyro_z_integral_deg_nominal=10, visual=dict(dx_px=20)),
            dict(index=1, eligible=False, repeat=0, direction='left',
                 gyro_z_integral_deg_nominal=10, visual=dict(dx_px=2000)),
            dict(index=2, eligible=True, repeat=1, direction='right',
                 gyro_z_integral_deg_nominal=-5, visual=dict(dx_px=-10)),
            dict(index=3, eligible=False, repeat=1, direction='right',
                 gyro_z_integral_deg_nominal=-5, visual=dict(dx_px=-1000)),
        ]
        ratio, fitted, checks = MotionValidation.compare_turns(results)
        self.assertEqual(ratio, 2)
        self.assertEqual(fitted, [0])
        self.assertEqual([check['index'] for check in checks], [2])
        self.assertEqual(checks[0]['difference_deg'], 0)

    def test_missing_camera_and_failed_run_are_retained(self):
        """Missing timed frames exclude a complete trial; run failure is explicit."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            logs, output = root/'logs'/'run', root/'analysis'
            logs.mkdir(parents=True)
            samples = [dict(sensor=sensor, request_ms=t, received_ms=t+1,
                            xyz=[0, 0, 1310] if sensor == 'gyro' else [0, 0, 16384])
                       for t in (-900, -500, 0, 200, 800, 1200)
                       for sensor in ('gyro', 'accel')]
            trial = dict(repeat=0, direction='left', early_stop=False, status='complete',
                         gyro_telemetry=samples, host_stop_elapsed_ms=250,
                         gyro_bias=dict(bias_raw_xyz=[0, 0, 0], accel_reference_raw_xyz=[0, 0, 16384]),
                         timed_frames=[], timed_folder=None, first='before.jpg', second='after.jpg')
            partial = dict(repeat=1, direction='left', status='incomplete', error='sensor timeout')
            (logs/'trials.json').write_text(json.dumps([trial, partial]), encoding='utf-8')
            (logs/'events.jsonl').write_text(json.dumps(dict(kind='failure', payload=dict(error='sensor timeout')))+'\n', encoding='utf-8')
            validator = MotionValidation(logs, output)
            with patch.object(validator.images, 'pair', return_value=dict(dx_px=40)):
                validator.run()
            result = json.loads((output/'validation.json').read_text(encoding='utf-8'))
            self.assertFalse(result['acquisition_complete'])
            self.assertEqual(len(result['trials']), 2)
            self.assertFalse(any(item['eligible'] for item in result['trials']))
            self.assertEqual(result['held_out'], [])
            self.assertIn('Missing timed camera evidence', result['trials'][0]['exclusion_reasons'])
            self.assertIn('Incomplete trial', result['trials'][1]['exclusion_reasons'][0])

    def test_partial_trial_is_accepted_by_other_report_commands(self):
        """Both legacy report interfaces retain a failed trial without images."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            logs, captures = root/'logs'/'run', root/'captures'/'run'
            logs.mkdir(parents=True)
            captures.mkdir(parents=True)
            partial = dict(repeat=0, direction='left', early_stop=False, pwm=60,
                           duration_ms=200, status='incomplete', error='preflight failed')
            (logs/'trials.json').write_text(json.dumps([partial]), encoding='utf-8')
            (logs/'events.jsonl').write_text('', encoding='utf-8')
            (captures/'frames.json').write_text('[]', encoding='utf-8')
            CalibrationAssessment(logs).run()
            IntegrationAssessment([logs], root/'integration').run()
            assessment = json.loads((root/'analysis'/'run'/'measurements.json').read_text(encoding='utf-8'))
            integration = json.loads((root/'integration'/'integration.json').read_text(encoding='utf-8'))
            self.assertEqual(assessment['trials'], [])
            self.assertEqual(assessment['unsupported_trials'][0]['reason'], 'preflight failed')
            self.assertEqual(integration['trials'][0]['unsupported'], 'preflight failed')


if __name__ == '__main__':
    unittest.main()
