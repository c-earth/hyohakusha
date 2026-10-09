"""Verify manifest inventory selection without hardware or image processing.

Synthetic project-local sessions test incomplete saved views, early stops, mixed
motion categories, missing status and optional validator evidence.
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.agent.analysis.capture_readiness import ReadinessAssessment


class ManifestInventoryTests(unittest.TestCase):
    """Own a project-local temporary manifest session for each focused check."""

    def setUp(self):
        """Create a temporary synthetic session entirely under the workspace."""
        self.temporary = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.session = Path(self.temporary.name)
        self.run = '20261009094004274'
        (self.session / 'logs' / self.run).mkdir(parents=True)
        (self.session / 'captures' / self.run).mkdir(parents=True)

    def tearDown(self):
        """Remove only this test's owned temporary session."""
        self.temporary.cleanup()

    def write_trials(self, trials):
        """Write supplied manifests and placeholder later files when requested."""
        (self.session / 'logs' / self.run / 'trials.json').write_text(json.dumps(trials))
        for trial in trials:
            if trial.get('later'):
                (self.session / 'captures' / self.run / trial['later']).write_bytes(b'placeholder')

    def test_incomplete_and_missing_status_saved_later_are_excluded(self):
        """Saved JPEG existence alone cannot classify incomplete motion as done."""
        self.write_trials([{'status': 'failed', 'later': 'failed.jpg'},
                           {'later': 'unknown.jpg'},
                           {'status': 'complete', 'later': 'complete.jpg'}])
        entries = ReadinessAssessment(self.session, self.session / 'output').inventory()
        self.assertEqual([entry['selected'] for entry in entries], [False, False, True])
        self.assertIsNone(entries[2]['validation_eligible'])

    def test_early_stop_and_mixed_directions_preserve_metadata(self):
        """Complete early-stop/turn captures remain categorized, not forward-only."""
        self.write_trials([{'status': 'complete', 'direction': 'forward', 'early_stop': True,
                            'later': 'early.jpg', 'duration_ms': 200},
                           {'status': 'complete', 'direction': 'right', 'early_stop': False,
                            'later': 'right.jpg'}])
        validation = self.session / 'analysis' / f'{self.run}-validation'
        validation.mkdir(parents=True)
        (validation / 'validation.json').write_text(json.dumps({'trials': [
            {'index': 0, 'eligible': False, 'pre_rest': {'accepted': True},
             'post_rest': {'accepted': False}}]}))
        entries = ReadinessAssessment(self.session, self.session / 'output').inventory()
        self.assertEqual([entry['direction'] for entry in entries], ['forward', 'right'])
        self.assertTrue(entries[0]['early_stop'])
        self.assertTrue(all(entry['selected'] for entry in entries))
        self.assertFalse(entries[0]['validation_eligible'])
        self.assertFalse(entries[0]['post_rest_accepted'])
        self.assertIsNone(entries[1]['validation_eligible'])

    def test_run_bound_excludes_newer_manifest(self):
        """Frozen run endpoint prevents later acquisition entering an assessment."""
        self.write_trials([{'status': 'complete', 'later': 'later.jpg'}])
        entries = ReadinessAssessment(self.session, self.session / 'output', '20261009093999999').inventory()
        self.assertEqual(entries, [])


if __name__ == '__main__':
    unittest.main()
