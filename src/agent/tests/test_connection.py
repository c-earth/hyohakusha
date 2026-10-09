"""Verify sequential host control with local byte queues and a synthetic clock.

No network connection, hardware command or real motion occurs. Tests exercise
the shared production transport and sampler, including the last pending read.
"""

import json
import threading
import unittest
from collections import deque
from unittest.mock import Mock, patch

from src.agent.tests.test_motion import FakeClock, FakeRecorder
from src.control.connection import RoverConnection
from src.control.motion import MotionSampler


class LocalSocket:
    """Record writes and queue sensor replies 60 ms later on a fake clock.

    pending counts issued sensor requests whose bytes have not been received.
    max_pending exposes accidental pipelining independently of host gate state.
    """

    def __init__(self, clock):
        """Keep the supplied monotonic clock; allocate only in-memory state."""
        self.clock = clock
        self.messages = []
        self.replies = deque()
        self.pending = self.max_pending = 0
        self.closed = False

    def sendall(self, data):
        """Record ASCII bytes and queue deterministic replies for test commands."""
        self.messages.append(data)
        if data == b'{Heartbeat}':
            return
        command = json.loads(data)
        if command['N'] in (1, 2, 3, 7, 8):
            self.pending += 1
            self.max_pending = max(self.pending, self.max_pending)
            content = '10,20,30' if command['N'] in (2, 3) else '7500'
            self.replies.append((self.clock()+0.06, ('{' + command['H'] + '_' + content + '}').encode(), True))
        elif command['N'] in (5, 6):
            self.replies.append((self.clock(), ('{' + command['H'] + '_ok}').encode(), False))

    def ready(self, readable, writable, exceptional, timeout):
        """Emulate select using queue deadlines, without OS descriptors."""
        return ([self] if self.replies and self.replies[0][0] <= self.clock() else [], [], [])

    def recv(self, size):
        """Return one ready local frame and decrement its pending sensor count."""
        _, data, sensor = self.replies.popleft()
        if len(data) > size:
            raise AssertionError('Unexpected fixture frame size')
        self.pending -= int(sensor)
        return data

    def close(self):
        """Mark the local fixture closed without any OS operation."""
        self.closed = True


class ConnectionTests(unittest.TestCase):
    """Check action ownership and pending reads across complete pulse execution."""

    def setUp(self):
        """Initialize a real connection object over a local socket substitute."""
        self.clock = FakeClock()
        self.owner = RoverConnection('unused.invalid')
        self.sock = LocalSocket(self.clock)
        self.owner.sock = self.sock
        self.owner.event = Mock()
        self.owner.duration_ms = 200
        self.owner.pwm = 60
        self.owner.imu_plan = 'adaptive'
        self.owner.heartbeat_at = self.clock()

    def test_pan_and_second_drive_refused_during_motion(self):
        """Only IMU and stop can follow N4 while its action remains reserved."""
        self.owner.send(dict(N=4, D1=3, D2=60, T=200))
        for command in (dict(N=4, D1=1, D2=60, T=200), dict(N=5, D1=1, D2=100),
                        dict(N=6, D1=1), dict(N=7, D1=2, T=30000), dict(N=1)):
            with self.subTest(command=command), self.assertRaises(RuntimeError):
                self.owner.send(command)
        self.assertEqual(len(self.sock.messages), 1)
        self.owner.send(dict(N=2))
        self.owner.send(dict(N=100))
        self.assertIsNone(self.owner._action)

    def test_one_sensor_and_stop_priority(self):
        """A pending IMU refuses a second read but cannot block N100."""
        self.owner.send(dict(N=2))
        with self.assertRaisesRegex(RuntimeError, 'one sensor'):
            self.owner.send(dict(N=3))
        self.owner.send(dict(N=100))
        self.assertEqual(json.loads(self.sock.messages[-1])['N'], 100)
        self.assertEqual(self.sock.pending, 1)

    def test_pan_blocks_drive_until_its_reply(self):
        """A matched pan acknowledgment releases command ownership only."""
        self.owner.send(dict(N=5, D1=1, D2=100))
        with self.assertRaises(RuntimeError):
            self.owner.send(dict(N=4, D1=3, D2=60, T=200))
        with patch('src.control.connection.select.select', side_effect=self.sock.ready):
            self.owner.poll()
        self.owner.send(dict(N=4, D1=3, D2=60, T=200))
        self.assertEqual(self.owner._action[0], 4)

    def test_second_controller_thread_cannot_write(self):
        """A competing worker receives an error before a socket write."""
        errors = []

        def compete():
            """Attempt one local write from a non-owner thread and record refusal."""
            try:
                self.owner.send(dict(N=5, D1=1, D2=100))
            except RuntimeError as error:
                errors.append(str(error))

        worker = threading.Thread(target=compete)
        worker.start()
        worker.join(timeout=1)
        self.assertFalse(worker.is_alive())
        self.assertEqual(len(errors), 1)
        self.assertEqual(self.sock.messages, [])

    def test_second_connection_refused_without_dialing(self):
        """An existing socket cannot be replaced by a second connect call."""
        with patch('src.control.connection.socket.create_connection') as dial:
            with self.assertRaisesRegex(RuntimeError, 'already owns'):
                self.owner.connect()
        dial.assert_not_called()

    def test_retagged_drive_ack_does_not_release_imu(self):
        """Installed-firmware expiry 'ok' must not permit a second IMU request."""
        tag = self.owner.send(dict(N=2))
        self.sock.replies.appendleft((self.clock(), ('{' + tag + '_ok}').encode(), False))
        with patch('src.control.connection.select.select', side_effect=self.sock.ready):
            self.owner.poll()
        with self.assertRaisesRegex(RuntimeError, 'one sensor'):
            self.owner.send(dict(N=3))
        self.clock.sleep(0.06)
        with patch('src.control.connection.select.select', side_effect=self.sock.ready):
            self.owner.poll()
        self.owner.send(dict(N=3))
        self.assertEqual(self.sock.max_pending, 1)

    def test_full_pulse_drains_last_imu_before_stopped_reads(self):
        """One owner allows camera observations and drains the final delayed read."""
        recorder = FakeRecorder([100.85, 100.95])
        sampler = MotionSampler(self.owner, clock=self.clock, sleep=self.clock.sleep)
        with patch('src.control.connection.time.monotonic', side_effect=self.clock), \
                patch('src.control.connection.time.monotonic_ns', side_effect=lambda: int(self.clock()*1e9)), \
                patch('src.control.connection.select.select', side_effect=self.sock.ready), \
                patch('src.control.connection.socket.create_connection') as dial:
            _, samples = sampler.run(1, False, recorder)
            self.assertIsNone(self.owner._pending_sensor)
            self.assertEqual(self.sock.pending, 0)
            self.owner.send(dict(N=1))
        dial.assert_not_called()
        commands = [json.loads(data)['N'] for data in self.sock.messages if data != b'{Heartbeat}']
        self.assertEqual(commands.count(4), 1)
        self.assertEqual(commands.count(100), 1)
        self.assertEqual(self.sock.max_pending, 1)
        self.assertTrue(samples)
        self.assertEqual(sampler.evidence['status'], 'complete')


if __name__ == '__main__':
    unittest.main()
