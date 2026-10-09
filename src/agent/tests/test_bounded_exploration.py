"""Check exploration pilot bounds without contacting rover hardware.

No CLI inputs. unittest emits test results; fake socket records bytes only.
Verifies command count/direction/duration and raw-echo-change stop behavior.
"""

import unittest
from argparse import Namespace
from unittest.mock import patch

from src.agent.runtime.bounded_exploration import BoundedExplorationSession
from src.agent.runtime.calibration_session import CalibrationSession
from src.control.connection import RoverConnection


class RecordedSocket:
    """Store outgoing bytes without network access; no constructor inputs."""

    def __init__(self):
        """Initialize byte-message list; no output/return value."""
        self.messages = []

    def sendall(self, data):
        """Record bytes input with no network/output; return None."""
        self.messages.append(data)


class ExplorationProbe(BoundedExplorationSession):
    """Use a supplied action tuple with in-memory commands and no files/network."""

    def __init__(self, actions=('forward', 'forward', 'forward')):
        """Initialize counters/socket only; no output/return value."""
        RoverConnection.__init__(self, 'unused.invalid')
        self.forward_commands = 0
        self.actions = actions
        self.movement_commands = 0
        self.compare_echo = True
        self.previous_echo = None
        self.sequence = 0
        self.sock = RecordedSocket()
        self.heartbeat_at = 0

    def event(self, kind, **payload):
        """Accept event kind/payload without file output; return None."""
        pass


class ExplorationBoundTests(unittest.TestCase):
    """Verify fixed pilot movement and stop gates; no inputs/hardware outputs."""

    def test_fourth_pulse_refused(self):
        """Exactly three forward pulses permitted; fourth rejected before send."""
        probe = ExplorationProbe()
        for _ in range(3):
            probe.send(dict(N=4, D1=3, D2=60, T=200))
            probe.send(dict(N=100))
        with self.assertRaises(ValueError):
            probe.send(dict(N=4, D1=3, D2=60, T=200))
        self.assertEqual(sum(b'"N":4' in message for message in probe.sock.messages), 3)

    def test_turn_or_duration_change_refused(self):
        """Refuse turn, increased duration and power before socket send."""
        for command in (dict(N=4, D1=1, D2=60, T=200), dict(N=4, D1=3, D2=60, T=300), dict(N=4, D1=3, D2=80, T=200)):
            probe = ExplorationProbe()
            with self.assertRaises(ValueError):
                probe.send(command)
            self.assertEqual(probe.sock.messages, [])

    def test_echo_shortening_stops(self):
        """A >90% echo shortening sends stop then raises; no return value."""
        probe = ExplorationProbe()
        with patch.object(CalibrationSession, 'sensors', side_effect=[dict(echo_us=10000), dict(echo_us=999)]):
            probe.sensors()
            with self.assertRaises(RuntimeError):
                probe.sensors()
        self.assertIn(b'"N":100', probe.sock.messages[-1])

    def test_echo_drop_boundary_and_stationary_variation_allowed(self):
        """Observed 31.7% variability and exactly 90% drops do not stop."""
        for previous, current in ((13349, 9117), (10000, 1000)):
            probe = ExplorationProbe()
            with self.subTest(previous=previous, current=current), patch.object(
                    CalibrationSession, 'sensors', side_effect=[dict(echo_us=previous), dict(echo_us=current)]):
                probe.sensors()
                self.assertEqual(probe.sensors()['echo_us'], current)
            self.assertEqual(probe.sock.messages, [])

    def test_mixed_plan_runs_once_in_exact_order(self):
        """A turn can collect calibration evidence within a three-action segment."""
        probe = ExplorationProbe(('forward', 'left', 'forward'))
        self.assertEqual(list(probe.trial_plan()), [(0, 'forward', 3, False),
                                                  (1, 'left', 1, False),
                                                  (2, 'forward', 3, False)])
        for number in (3, 1, 3):
            probe.send(dict(N=4, D1=number, D2=60, T=200))
            probe.send(dict(N=100))
        self.assertEqual(probe.movement_commands, 3)
        self.assertEqual(probe.forward_commands, 2)
        with self.assertRaises(ValueError):
            probe.send(dict(N=4, D1=3, D2=60, T=200))

    def test_action_order_is_enforced(self):
        """Even an allowed turn is refused when the next frozen action is forward."""
        probe = ExplorationProbe(('forward', 'left'))
        with self.assertRaisesRegex(ValueError, 'frozen plan'):
            probe.send(dict(N=4, D1=1, D2=60, T=200))
        self.assertEqual(probe.movement_commands, 0)
        self.assertEqual(probe.sock.messages, [])

    def test_invalid_plan_rejected_before_session_creation(self):
        """Overlong routes and reverse are rejected before file or network use."""
        for actions in ([], ['forward']*4, ['backward']):
            with self.subTest(actions=actions), self.assertRaisesRegex(ValueError, '1-3'):
                BoundedExplorationSession(Namespace(actions=actions))

    def test_turn_resets_echo_comparison_for_new_heading(self):
        """Raw echo values at different headings cannot be treated as approach."""
        probe = ExplorationProbe(('left', 'forward'))
        probe.previous_echo = 10000
        with patch.object(CalibrationSession, 'acquire_trial') as acquire, \
                patch.object(CalibrationSession, 'sensors', side_effect=[dict(echo_us=4000), dict(echo_us=399)]):
            probe.acquire_trial(0, 'left', 1, False)
            self.assertIsNone(probe.previous_echo)
            probe.sensors()
            probe.acquire_trial(1, 'forward', 3, False)
            with self.assertRaises(RuntimeError):
                probe.sensors()
        self.assertEqual(acquire.call_count, 2)


if __name__ == '__main__':
    unittest.main()
