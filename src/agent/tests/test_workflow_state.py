"""Verify conservative pulse accounting, idempotent imports and durable state locks."""

import json
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from src.agent.analysis.workflow_state import WorkflowState


class WorkflowStateTests(unittest.TestCase):
    """Synthetic saved events never contact a controller."""

    def test_attempts_distinct_from_completions_and_idempotent_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            store = WorkflowState(session / 'analysis' / 'state.json')
            state = store.create(session, 'observe', 9, 3)
            self.assertEqual(state['status'], 'not_started')
            self.assertFalse(state['live_authorized'])
            run = session / 'logs' / '001'
            run.mkdir(parents=True)
            (run / 'trials.json').write_text('[{"status":"complete"}]')
            events = [dict(kind='send', payload=dict(message='{"N":4}', complete_ns=1)),
                      dict(kind='send', payload=dict(message='{"N":4}')),
                      dict(kind='cleanup', payload=dict(stop_attempted=True, socket_closed=True, stop_error=None)),
                      dict(kind='complete', payload={})]
            (run / 'events.jsonl').write_text('\n'.join(json.dumps(event) for event in events))
            first = store.import_run('001')
            self.assertEqual(first['accounting']['attempted_n4_lower_bound'], 2)
            self.assertEqual(first['accounting']['unknown_send_results'], 1)
            self.assertIsNone(first['processed_completed_run_cutoff'])
            self.assertEqual(first['runs']['001']['completed_manifest_trials'], 1)
            self.assertEqual(first, store.import_run('001'))
            (run / 'events.jsonl').write_text('broken')
            with self.assertRaises(ValueError):
                store.import_run('001')

    def test_lock_overwrite_and_raw_output_protection(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            with self.assertRaises(ValueError):
                WorkflowState(session / 'logs' / 'state.json').create(session, 'x', 1, 1)
            store = WorkflowState(session / 'state.json')
            store.create(session, 'x', 1, 1)
            with self.assertRaises(FileExistsError):
                store.create(session, 'x', 1, 1)
            store.lock.write_text('busy')
            with self.assertRaises(FileExistsError):
                store.request('jar', 'another view')
            self.assertEqual(store.status()['backlog'], {})

    def test_backlog_workers_missing_events_and_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = WorkflowState(Path(temporary) / 'state.json')
            store.create(temporary, 'x', 6, 2)
            store.request('jar', 'another view')
            store.worker('images', 'offline cutoff001', 'running')
            state = store.import_run('001')
            self.assertFalse(state['accounting']['complete'])
            self.assertEqual(state['revision'], 4)
            self.assertEqual(state['workers']['images']['status'], 'running')

    def test_zero_scope_and_reservation_caps_idempotency(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            store = WorkflowState(session / 'state.json')
            with self.assertRaises(ValueError):
                store.create(session, 'x', 0, 1)
            store.create(session, 'unselected', 0, 0)
            with self.assertRaises(ValueError):
                store.reserve('a', ['forward'])
            selected = WorkflowState(session / 'proposal.json')
            selected.create(session, 'proposal', 3, 1)
            first = selected.reserve('a', ['left', 'forward', 'right'])
            self.assertEqual(first, selected.reserve('a', ['left', 'forward', 'right']))
            self.assertEqual(first['budget']['remaining_pulses'], 0)
            self.assertFalse(first['live_authorized'])
            with self.assertRaises(ValueError):
                selected.reserve('b', ['forward'])
            with self.assertRaises(ValueError):
                selected.reserve('a', ['right'])

    def test_deadline_and_unknown_accounting_block_reservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            expired = WorkflowState(session / 'expired.json')
            expired.create(session, 'proposal', 3, 2, '2026-10-09T12:00:00+00:00')
            with self.assertRaises(ValueError):
                expired.reserve('a', ['forward'], datetime(2026, 10, 9, 12, tzinfo=timezone.utc))
            unknown = WorkflowState(session / 'unknown.json')
            unknown.create(session, 'proposal', 3, 2)
            unknown.import_run('001')
            with self.assertRaises(ValueError):
                unknown.reserve('a', ['forward'])

    def test_linked_and_disjoint_budgets_and_association_protection(self):
        with tempfile.TemporaryDirectory() as temporary:
            session = Path(temporary)
            for stamp in ('001', '002'):
                run = session / 'logs' / stamp
                run.mkdir(parents=True)
                (run / 'trials.json').write_text(json.dumps([dict(status='complete')] * 3))
                events = [dict(kind='send', payload=dict(message='{"N":4,"D1":3}', complete_ns=1))] * 3
                events += [dict(kind='complete', payload={}), dict(kind='cleanup', payload=dict(stop_attempted=True, socket_closed=True, stop_error=None))]
                (run / 'events.jsonl').write_text('\n'.join(json.dumps(event) for event in events))
            disjoint = WorkflowState(session / 'disjoint.json')
            disjoint.create(session, 'proposal', 6, 2)
            disjoint.import_run('001')
            state = disjoint.reserve('new', ['forward'] * 3)
            self.assertEqual(state['budget']['consumed_pulses'], 6)
            linked = WorkflowState(session / 'linked.json')
            linked.create(session, 'proposal', 6, 2)
            linked.reserve('a', ['forward'] * 3)
            state = linked.import_run('001', 'a')
            self.assertEqual(state['budget']['consumed_pulses'], 3)
            self.assertEqual(state, linked.import_run('001', 'a'))
            with self.assertRaises(ValueError):
                linked.import_run('002', 'a')
            with self.assertRaises(ValueError):
                linked.import_run('001')
            mismatch = WorkflowState(session / 'mismatch.json')
            mismatch.create(session, 'proposal', 6, 2)
            mismatch.reserve('a', ['left'] * 3)
            mismatch.import_run('001', 'a')
            with self.assertRaises(ValueError):
                mismatch.reserve('b', ['forward'])


if __name__ == '__main__':
    unittest.main()
