"""Exercise evidence predicates and output protection without hardware."""

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from src.agent.analysis.review_segment import SegmentReview


class SegmentReviewTests(unittest.TestCase):
    """Reporting success and acknowledged commands cannot replace missing rest."""

    def test_support_requires_explicit_nonempty_complete_rest(self):
        validation = dict(trials=[dict(status='complete', pre_rest=dict(accepted=True), post_rest=dict(accepted=True))],
                          acquisition_complete=True, cleanup_recorded=True, event_errors=[], acquisition_failures=[])
        inventory = dict(trials=1, acquisition_complete=True, positive_cleanup=True,
                         read_errors=[], failures=[], minimum_battery_v=7.5)
        self.assertTrue(SegmentReview.evidence_card(validation, inventory)['saved_evidence_supported'])
        for field, value in [('status', 'unknown'), ('post_rest', dict(accepted=False))]:
            changed = deepcopy(validation)
            changed['trials'][0][field] = value
            self.assertFalse(SegmentReview.evidence_card(changed, inventory)['saved_evidence_supported'])
        for changed in ({}, dict(validation, trials=[]), dict(validation, event_errors=['broken'])):
            self.assertFalse(SegmentReview.evidence_card(changed, inventory)['saved_evidence_supported'])
        for battery in (None, 6.9, float('nan')):
            self.assertFalse(SegmentReview.evidence_card(validation, dict(inventory, minimum_battery_v=battery))['saved_evidence_supported'])

    def test_raw_output_and_existing_output_are_protected(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            for category in ('logs', 'captures'):
                with self.assertRaises(ValueError):
                    SegmentReview(session, '001', session / category / 'bad')
            output = session / 'analysis' / 'existing'
            output.mkdir(parents=True)
            with self.assertRaises(FileExistsError):
                SegmentReview(session, '001', output).assess()

    def test_missing_run_retains_unsupported_card(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            output = session / 'analysis' / 'missing'
            card = SegmentReview(session, '001', output).assess()
            self.assertFalse(card['saved_evidence_supported'])
            self.assertIsNotNone(card['validation_error'])
            self.assertTrue((output / 'decision.json').is_file())


if __name__ == '__main__':
    unittest.main()
