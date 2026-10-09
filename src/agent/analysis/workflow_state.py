"""Maintain offline coordinator memory; state never authorizes hardware operations.

JSON state holds mission caps, worker assignments, requested-view backlog and
saved-run accounting. Mutations lock the state and replace it atomically; history
is append-only within that JSON. N4 event sends count attempts conservatively,
including sends whose completion bracket is unknown; manifests count completions.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from src.agent.analysis.session_brief import SessionBrief


class WorkflowState:
    """Persist offline state at path, serializing read-modify-write transactions.

    path must be outside its session's raw logs/captures. A concurrent or stale
    lock refuses mutation rather than risking lost updates. Same unchanged run
    import is idempotent; changed saved files are refused for explicit review.
    """

    def __init__(self, path):
        """Resolve the state file and derive its exclusive transaction lock."""
        self.path = Path(path).resolve()
        self.lock = self.path.with_suffix(self.path.suffix + '.lock')

    def transact(self, operation, creating=False):
        """Lock, load, apply operation and atomically save; never overwrite on create."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        temporary = None
        try:
            os.close(descriptor)
            if creating and self.path.exists():
                raise FileExistsError(self.path)
            state = {} if creating else self.status()
            updated = operation(state)
            if updated is None:
                return state
            session = Path(updated['session']).resolve()
            if any(self.path.is_relative_to(session / kind) for kind in ('logs', 'captures')):
                raise ValueError('State must be outside raw logs/captures')
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=self.path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(updated, stream, indent=2, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
            return updated
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            self.lock.unlink(missing_ok=True)

    def status(self):
        """Read current saved state without changing its history or revision."""
        return json.loads(self.path.read_text(encoding='utf-8'))

    @staticmethod
    def history(state, action, details):
        """Append a UTC event and increment state revision for one committed change."""
        state['revision'] += 1
        state['history'].append(dict(utc=datetime.now(timezone.utc).isoformat(), action=action, details=details))
        return state

    def create(self, session, objective, max_pulses, max_segments, deadline=None, max_echo_retries=3):
        """Create a proposal; zero/zero caps mean no live round has been selected."""
        session = Path(session).resolve()
        if any(self.path.is_relative_to(session / kind) for kind in ('logs', 'captures')):
            raise ValueError('State must be outside raw logs/captures')
        if max_pulses < 0 or max_segments < 0 or (max_pulses == 0) != (max_segments == 0) or not 0 <= max_echo_retries <= 3:
            raise ValueError('Caps must both be positive or both zero; 0–3 echo retries required')
        if deadline:
            instant = datetime.fromisoformat(deadline)
            if instant.tzinfo is None:
                raise ValueError('Deadline must include UTC offset')
        state = dict(schema_version=1, revision=0, session=str(session), status='not_started',
                     live_authorized=False, mission=dict(objective=objective, max_attempted_pulses=max_pulses,
                     max_segments=max_segments, deadline=deadline, max_echo_retries=max_echo_retries,
                     pwm=60, duration_ms=200, actions=['forward', 'left', 'right']),
                     runs={}, reservations={}, processed_completed_run_cutoff=None, backlog={}, workers={}, history=[],
                     limitations=['State stores proposals, not human authorization.',
                                  'Reservation budgets are bookkeeping; live launchers do not automatically enforce them.'])
        return self.transact(lambda unused: self.history(state, 'create', {'proposal_only': True}), creating=True)

    def import_run(self, run, reservation_id=None):
        """Import a numeric saved run once; attempts and unknown outcomes stay distinct."""
        if not str(run).isdigit():
            raise ValueError('Run must be numeric')
        def operation(state):
            reader = SessionBrief(state['session'])
            folder = Path(state['session']) / 'logs' / run
            inventory = reader.run_summary(folder)
            attempts, unknown, errors, directions = 0, 0, [], []
            events = folder / 'events.jsonl'
            if events.exists():
                try:
                    for number, line in enumerate(reader.read(events).splitlines(), 1):
                        try:
                            event = json.loads(line)
                            if not isinstance(event, dict):
                                raise ValueError('event object required')
                            if event.get('kind') != 'send':
                                continue
                            payload = event.get('payload', {})
                            message = payload.get('message')
                            if not isinstance(message, str):
                                raise ValueError('send message missing')
                            message = message.strip()
                            if message == '{Heartbeat}':
                                continue
                            command = json.loads(message)
                            if command.get('N') == 4:
                                attempts += 1
                                directions.append({1: 'left', 2: 'right', 3: 'forward', 4: 'backward'}.get(command.get('D1'), 'unknown'))
                                if payload.get('complete_ns') is None:
                                    unknown += 1
                        except (ValueError, TypeError, AttributeError):
                            errors.append(f'Unknown event/send at line {number}')
                except (OSError, UnicodeError) as error:
                    errors.append(str(error))
            else:
                errors.append('Missing events; attempted motion count unknown')
            record = dict(attempted_n4_lower_bound=attempts, unknown_send_results=unknown,
                          accounting_complete=bool(not errors and not unknown and inventory['acquisition_complete']
                                                   and attempts == inventory['counts'].get('complete', 0)),
                          accounting_errors=errors,
                          completed_manifest_trials=inventory['counts'].get('complete', 0),
                          inventory=inventory, sources_sha256=reader.sources,
                          limitations=['Send events are logged after socket send; unlogged failed sends may have partially reached hardware.',
                                       'Recorded N4 count is a lower bound, not a proven total of attempted hardware motion.'])
            record.update(reservation_id=reservation_id, recorded_actions=directions)
            if reservation_id is not None:
                reservation = state.get('reservations', {}).get(reservation_id)
                if reservation is None:
                    raise ValueError('Unknown reservation ID')
                if any(item.get('reservation_id') == reservation_id for name, item in state['runs'].items() if name != run):
                    raise ValueError('Reservation already linked to another run')
                record['reservation_matches'] = directions == reservation['actions']
                if not record['reservation_matches']:
                    record['accounting_complete'] = False
                    record['accounting_errors'].append('Recorded N4 directions/order do not match frozen reservation')
            if run in state['runs']:
                if (state['runs'][run]['sources_sha256'] == record['sources_sha256']
                        and state['runs'][run].get('reservation_id') == reservation_id):
                    return None
                raise ValueError('Imported run changed; explicit review required')
            state['runs'][run] = record
            if record['accounting_complete'] and inventory['trials'] > 0:
                state['processed_completed_run_cutoff'] = max(run, state['processed_completed_run_cutoff'] or run)
            state['accounting'] = dict(attempted_n4_lower_bound=sum(item['attempted_n4_lower_bound'] for item in state['runs'].values()),
                                      unknown_send_results=sum(item['unknown_send_results'] for item in state['runs'].values()),
                                      imported_segments=len(state['runs']),
                                      complete=all(item['accounting_complete'] for item in state['runs'].values()))
            self.update_budget(state)
            return self.history(state, 'import-run', {'run': run})
        return self.transact(operation)

    def request(self, identifier, description, status='pending'):
        """Create or update an opportunistic data request without selecting a route."""
        if status not in ('pending', 'collected', 'deferred', 'cancelled'):
            raise ValueError('Invalid request status')
        def operation(state):
            state['backlog'][identifier] = dict(description=description, status=status)
            return self.history(state, 'request', {'id': identifier, 'status': status})
        return self.transact(operation)

    def worker(self, identifier, assignment, status):
        """Record a native worker assignment/status; never spawn or message an agent."""
        if status not in ('idle', 'running', 'completed', 'interrupted', 'failed', 'unknown'):
            raise ValueError('Invalid worker status')
        def operation(state):
            state['workers'][identifier] = dict(assignment=assignment, status=status)
            return self.history(state, 'worker', {'id': identifier, 'status': status})
        return self.transact(operation)

    def reserve(self, identifier, actions, now=None):
        """Consume a frozen 1–3-action bookkeeping budget before any external dispatch.

        No hardware is dispatched and live_authorized never changes. An unchanged
        reservation ID is idempotent. Failed/missing/unknown imported accounting
        blocks new reservations. Full reservations plus unlinked run lower bounds
        consume budget; explicit run associations prevent counting motion twice.
        """
        actions = list(actions)
        if not identifier or not 1 <= len(actions) <= 3 or any(action not in ('forward', 'left', 'right') for action in actions):
            raise ValueError('Reservation requires an ID and 1–3 forward/left/right actions')
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ValueError('Reservation time must include UTC offset')
        def operation(state):
            reservations = state.setdefault('reservations', {})
            if identifier in reservations:
                if reservations[identifier]['actions'] != actions:
                    raise ValueError('Reservation ID already has another frozen plan')
                return None
            if state.get('runs') and not state.get('accounting', {}).get('complete', False):
                raise ValueError('Imported run accounting is incomplete/unknown; review before reserving')
            mission = state['mission']
            if mission['deadline'] and instant >= datetime.fromisoformat(mission['deadline']):
                raise ValueError('Mission deadline reached')
            self.update_budget(state)
            pulses, segments = state['budget']['consumed_pulses'], state['budget']['consumed_segments']
            if pulses + len(actions) > mission['max_attempted_pulses'] or segments + 1 > mission['max_segments']:
                raise ValueError('Proposal pulse/segment budget exhausted or not selected')
            reservations[identifier] = dict(actions=actions, pulse_count=len(actions),
                                             reserved_utc=instant.isoformat(), live_authorized=False)
            self.update_budget(state)
            return self.history(state, 'reserve', {'id': identifier, 'actions': actions, 'bookkeeping_only': True})
        return self.transact(operation)

    @staticmethod
    def update_budget(state):
        """Charge full reservations plus disjoint unlinked imported run evidence."""
        reservations = state.get('reservations', {})
        unlinked = [item for item in state.get('runs', {}).values() if item.get('reservation_id') is None]
        linked_excess = sum(max(0, item['attempted_n4_lower_bound'] - len(reservations[item['reservation_id']]['actions']))
                            for item in state.get('runs', {}).values() if item.get('reservation_id') in reservations)
        pulses = sum(len(item['actions']) for item in reservations.values()) + sum(item['attempted_n4_lower_bound'] for item in unlinked) + linked_excess
        segments = len(reservations) + len(unlinked)
        state['budget'] = dict(consumed_pulses=pulses, consumed_segments=segments,
                               remaining_pulses=state['mission']['max_attempted_pulses']-pulses,
                               remaining_segments=state['mission']['max_segments']-segments)


def main():
    """Expose offline state, run import, request, worker and budget-reservation commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('create')
    create.add_argument('--session', type=Path, required=True)
    create.add_argument('--objective', required=True)
    create.add_argument('--max-pulses', type=int, required=True)
    create.add_argument('--max-segments', type=int, required=True)
    create.add_argument('--deadline')
    create.add_argument('--max-echo-retries', type=int, default=3)
    commands.add_parser('status')
    imported = commands.add_parser('import-run')
    imported.add_argument('--run', required=True)
    imported.add_argument('--reservation-id')
    reserve = commands.add_parser('reserve')
    reserve.add_argument('--id', required=True)
    reserve.add_argument('--actions', required=True, help='Comma-separated frozen 1–3 directions')
    for command in ('request', 'update-request'):
        request = commands.add_parser(command)
        request.add_argument('--id', required=True)
        request.add_argument('--description', required=True)
        request.add_argument('--status', choices=('pending', 'collected', 'deferred', 'cancelled'), default='pending')
    worker = commands.add_parser('worker')
    worker.add_argument('--id', required=True)
    worker.add_argument('--assignment', required=True)
    worker.add_argument('--status', required=True)
    args = parser.parse_args()
    store = WorkflowState(args.state)
    if args.command == 'create':
        result = store.create(args.session, args.objective, args.max_pulses, args.max_segments, args.deadline, args.max_echo_retries)
    elif args.command == 'status':
        result = store.status()
    elif args.command == 'import-run':
        result = store.import_run(args.run, args.reservation_id)
    elif args.command == 'worker':
        result = store.worker(args.id, args.assignment, args.status)
    elif args.command == 'reserve':
        result = store.reserve(args.id, args.actions.split(','))
    else:
        result = store.request(args.id, args.description, args.status)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
