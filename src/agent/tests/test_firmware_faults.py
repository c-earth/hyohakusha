"""Exercise UNO fault handling through real host parsing and fake transports.

No sockets or rover actions occur. Inputs include fragmented frames and errors
for an N4 tag while IMU collection is active; outputs stay in memory.
"""

import unittest
from collections import deque
from unittest.mock import Mock, patch

from src.agent.runtime.calibration_session import CalibrationSession
from src.control.connection import RoverConnection
from src.control.motion import MotionSampler
from src.control.protocol import FirmwareFault
from src.agent.tests.test_motion import FakeClock, FakeOwner


class ChunkSocket:
    """Supply queued byte chunks locally, preserving packet fragmentation."""

    def __init__(self, chunks):
        """Store byte chunks in order without opening a socket."""
        self.chunks = deque(chunks)

    def recv(self, size):
        """Return the next synthetic chunk, no larger than requested size."""
        chunk = self.chunks.popleft()
        if len(chunk) > size:
            self.chunks.appendleft(chunk[size:])
        return chunk[:size]


class ReplyProbe(CalibrationSession):
    """Run production poll/request parsing without session files or network."""

    def __init__(self, chunks):
        """Initialize just the receive state and an in-memory event recorder."""
        RoverConnection.__init__(self, 'unused.invalid')
        self.sock = ChunkSocket(chunks)
        self.buffer = ''
        self.last_receive_ns = None
        self.event = Mock()
        self.send = Mock(return_value='c1')


class FirmwareMotionOwner(FakeOwner, RoverConnection):
    """Feed one N4 or IMU fault through the production session parser.

    fault_number selects N4 rejection or N2 read failure. Production poll runs
    over local chunks, while the parent owns deterministic command timing.
    """

    poll = CalibrationSession.poll

    def __init__(self, clock, fault_number):
        """Store fake transport state and select the command that will fail."""
        RoverConnection.__init__(self, 'unused.invalid')
        super().__init__(clock)
        self.fault_number = fault_number
        self.sock = ChunkSocket([])
        self.buffer = ''
        self.last_receive_ns = None

    def send(self, command):
        """Record transmission and queue a tagged error or normal IMU reply."""
        tag = super().send(command)
        if isinstance(command, dict) and command['N'] == self.fault_number:
            self.replies.clear()
            self.replies.append('{' + tag + '_error_imu_read}')
        if self.replies:
            self.sock.chunks.append(''.join(self.replies).encode('ascii'))
            self.replies.clear()
        return tag

    def select_ready(self, readable, writable, exceptional, timeout):
        """Return readiness of queued bytes; never inspect OS descriptors."""
        return ([self.sock] if self.sock.chunks else [], [], [])


class FirmwareFaultTests(unittest.TestCase):
    """Verify faults cannot become sensor values, bias retries or ignored tags."""

    def test_success_frames_remain_compatible(self):
        """Existing heartbeat, acknowledgment and raw sensor formats pass."""
        for frame in ('{Heartbeat}', '{ok}', '{c1_ok}', '{c2_-32768,0,32767}',
                      '{battery_v_7.500}', '{ultrasound_us_1234}'):
            with self.subTest(frame=frame):
                self.assertIsNone(FirmwareFault.check_frame(frame))

    def test_tagged_and_untagged_fault_fields(self):
        """Keep the firmware reason and optional request tag on RuntimeError."""
        for frame, tag, reason in (('{c1_error_imu_read}', 'c1', 'imu_read'),
                                   ('{gyro_raw_xyz_error_imu_not_ready}', 'gyro_raw_xyz', 'imu_not_ready'),
                                   ('{error_bad_json}', None, 'bad_json')):
            with self.subTest(frame=frame), self.assertRaises(FirmwareFault) as result:
                FirmwareFault.check_frame(frame)
            self.assertEqual(result.exception.tag, tag)
            self.assertEqual(result.exception.reason, reason)
            self.assertNotIsInstance(result.exception, ValueError)

    def test_fragmented_fault_is_logged_and_rejected(self):
        """A split tagged error faults only once its complete frame arrives."""
        probe = ReplyProbe([b'{c4_error_', b'imu_read}'])
        with patch('src.control.connection.select.select',
                   return_value=([probe.sock], [], [])):
            self.assertEqual(probe.poll(), [])
            with self.assertRaisesRegex(FirmwareFault, 'imu_read'):
                probe.poll()
        self.assertEqual(probe.event.call_args.kwargs['message'], '{c4_error_imu_read}')

    def test_stationary_request_rejects_unrelated_fault(self):
        """N4 errors cannot hide behind a currently awaited IMU request tag."""
        probe = ReplyProbe([b'{old_drive_error_imu_not_ready}{c1_1,2,3}'])
        with patch('src.control.connection.select.select',
                   return_value=([probe.sock], [], [])):
            with self.assertRaisesRegex(FirmwareFault, 'old_drive'):
                probe.request({'N': 2})

    def test_motion_fault_attempts_stop_and_retains_error(self):
        """A refused N4 or failed active IMU read triggers immediate N100 cleanup."""
        for number in (4, 2):
            with self.subTest(command=number):
                clock = FakeClock()
                owner = FirmwareMotionOwner(clock, number)
                sampler = MotionSampler(owner, clock=clock, sleep=clock.sleep)
                with patch('src.control.connection.select.select', side_effect=owner.select_ready), \
                        patch('src.control.connection.time.monotonic_ns',
                              side_effect=lambda: int(clock() * 1e9)):
                    with self.assertRaisesRegex(FirmwareFault, 'imu_read'):
                        sampler.run(1, False)
                self.assertEqual(owner.command_numbers()[-1], 100)
                self.assertEqual(owner.command_numbers().count(4), 1)
                self.assertEqual(sampler.evidence['status'], 'incomplete')
                self.assertIn('Firmware fault', sampler.evidence['error'])
                self.assertLess(sampler.evidence['stop_elapsed_ms'], 200)

    def test_gyro_fault_is_not_retried_as_stationarity_rejection(self):
        """Explicit IMU failure bypasses the three stopped bias attempts."""
        probe = ReplyProbe([])
        probe.measure_gyro_bias = Mock(side_effect=FirmwareFault('c1', 'imu_not_ready'))
        with self.assertRaises(FirmwareFault):
            probe.calibrate_gyro()
        probe.measure_gyro_bias.assert_called_once()


if __name__ == '__main__':
    unittest.main()
