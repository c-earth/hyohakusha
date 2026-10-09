"""Check missing evidence, failure retention and frozen offline session counts."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from src.agent.analysis.session_brief import SessionBrief


class SessionBriefTests(unittest.TestCase):
    """Use temporary saved records; tests never open network connections."""

    def test_complete_and_unknown_status_and_cutoff(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            for stamp in ('001', '002'):
                folder = session / 'logs' / stamp
                folder.mkdir(parents=True)
                (folder / 'trials.json').write_text(json.dumps([dict(status='complete', direction='forward', after=dict(echo_us=1000)), {}]))
                events = [dict(kind='battery', payload=dict(voltage_v=7.5)), dict(kind='complete', payload={}),
                          dict(kind='cleanup', payload=dict(stop_attempted=True, socket_closed=True, stop_error=None))]
                (folder / 'events.jsonl').write_text('\n'.join(json.dumps(event) for event in events))
            result = SessionBrief(session, '001').assess()
            self.assertEqual(result['counts'], dict(complete=1, unknown=1))
            self.assertEqual(len(result['runs']), 1)
            self.assertTrue(result['runs'][0]['positive_cleanup'])
            self.assertFalse(result['runs'][0]['acquisition_complete'])
            self.assertAlmostEqual(result['runs'][0]['approximate_echo_distance_m'], 0.1715)

    def test_malformed_events_and_missing_cleanup_remain_visible(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary) / 'logs' / '001'
            folder.mkdir(parents=True)
            (folder / 'trials.json').write_text('[{"status":"failed","error":"refused"}]')
            (folder / 'events.jsonl').write_text('{"kind":"failure","payload":{"error":"refused"}}\nbroken')
            run = SessionBrief(Path(temporary)).assess()['runs'][0]
            self.assertFalse(run['positive_cleanup'])
            self.assertFalse(run['acquisition_complete'])
            self.assertEqual(len(run['failures']), 1)
            self.assertEqual(len(run['read_errors']), 1)
            self.assertIsNone(run['cleanup'])

    def test_echo_unknown_is_not_zero_clearance(self):
        for value in (0, -1, None, '1000', float('nan'), True):
            self.assertIsNone(SessionBrief.distance(value))

    def test_cli_output_protects_raw_and_existing_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            folder = session / 'logs' / '001'
            folder.mkdir(parents=True)
            trial = dict(status='complete', direction='forward', before=dict(echo_us=1000),
                         after=dict(echo_us=750), host_stop_elapsed_ms=250)
            (folder / 'trials.json').write_text(json.dumps([trial]))
            (folder / 'events.jsonl').write_text('')
            base = [sys.executable, '-B', '-m', 'src.agent.analysis.session_brief', str(session), '--output']
            raw = subprocess.run(base + [str(folder / 'bad')], capture_output=True, text=True)
            self.assertNotEqual(raw.returncode, 0)
            self.assertFalse((folder / 'bad').exists())
            output = session / 'analysis' / 'brief'
            success = subprocess.run(base + [str(output)], capture_output=True, text=True)
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertIn(str((output / 'report.html').resolve()), success.stdout)
            report = json.loads((output / 'summary.json').read_text())
            self.assertEqual(report['runs'][0]['observations'][0]['echo_change_percent'], -25)
            self.assertEqual(report['runs'][0]['observations'][0]['host_stop_elapsed_ms'], 250)
            original = (output / 'summary.json').read_bytes()
            refused = subprocess.run(base + [str(output)], capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(original, (output / 'summary.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
