"""Check exploration pilot bounds without contacting rover hardware.

No CLI inputs. unittest emits test results; fake socket records bytes only.
Verifies command count/direction/duration and raw-echo-change stop behavior.
"""

import unittest
from unittest.mock import patch

from bounded_exploration import BoundedExplorationSession
from calibration_session import CalibrationSession


class RecordedSocket:
    """Store outgoing bytes without network access; no constructor inputs."""

    def __init__(self):
        """Initialize byte-message list; no output/return value."""
        self.messages = []

    def sendall(self, data):
        """Record bytes input with no network/output; return None."""
        self.messages.append(data)


class ExplorationProbe(BoundedExplorationSession):
    """Construct command-gate test fixture without files/network; no inputs."""

    def __init__(self):
        """Initialize counters/socket only; no output/return value."""
        self.forward_commands = 0
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
        with self.assertRaises(ValueError):
            probe.send(dict(N=4, D1=3, D2=60, T=200))
        self.assertEqual(len(probe.sock.messages), 3)

    def test_turn_or_duration_change_refused(self):
        """Refuse turn, increased duration and power before socket send."""
        for command in (dict(N=4, D1=1, D2=60, T=200), dict(N=4, D1=3, D2=60, T=300), dict(N=4, D1=3, D2=80, T=200)):
            probe = ExplorationProbe()
            with self.assertRaises(ValueError):
                probe.send(command)
            self.assertEqual(probe.sock.messages, [])

    def test_echo_shortening_stops(self):
        """A >20% echo shortening sends stop then raises; no return value."""
        probe = ExplorationProbe()
        with patch.object(CalibrationSession, 'sensors', side_effect=[dict(echo_us=10000), dict(echo_us=7900)]):
            probe.sensors()
            with self.assertRaises(RuntimeError):
                probe.sensors()
        self.assertIn(b'"N":100', probe.sock.messages[-1])


if __name__ == '__main__':
    unittest.main()
