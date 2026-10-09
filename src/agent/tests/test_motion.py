"""Exercise pulse ordering and fault evidence with a fake monotonic clock.

The owner records command dictionaries and supplies synthetic IMU replies.
No sockets, rover commands, real waits or output files are used by these tests.
"""

import unittest
from collections import deque

from src.control.motion import MotionSampler


class FakeClock:
    """Advance seconds only through sleep or a configured skipped interval.

    start is the initial monotonic time in seconds. skip, when supplied, is a
    (begin, end) interval that one sleep jumps across to mimic a delayed wake.
    """

    def __init__(self, start=100.0, skip=None):
        """Store seconds and an optional one-time scheduling delay."""
        self.now = start
        self.skip = skip

    def __call__(self):
        """Return the current synthetic monotonic seconds without advancing."""
        return self.now

    def sleep(self, seconds):
        """Advance by seconds, jumping across the configured interval once."""
        target = self.now + seconds
        if self.skip is not None and target >= self.skip[0]:
            target = max(target, self.skip[1])
            self.skip = None
        self.now = target


class FakeRecorder:
    """Expose completed frame brackets without starting an HTTP worker.

    received_seconds lists synthetic monotonic receipt times. epoch_ns is set
    by the sampler; error remains None unless the test explicitly changes it.
    """

    def __init__(self, received_seconds):
        """Convert receipt seconds into camera metadata for snapshot calls."""
        self.frames = [dict(file=f'frame-{index}.jpg',
                            request_ns=int((seconds - 0.02) * 1e9),
                            received_ns=int(seconds * 1e9))
                       for index, seconds in enumerate(received_seconds)]
        self.epoch_ns = None
        self.error = None

    def snapshot(self):
        """Return detached frame dictionaries, matching the recorder contract."""
        return [dict(frame) for frame in self.frames]


class FakeOwner:
    """Record control order and supply local sensor frames through poll.

    clock supplies synthetic monotonic seconds. respond=False withholds IMU
    replies. poll_delay advances time once during polling to exercise overdue
    stops. Commands, event payloads and transport brackets remain in memory.
    """

    def __init__(self, clock, respond=True, poll_delay=0.0):
        """Initialize a PWM60/T200 owner with no network or file handles."""
        self.clock = clock
        self.respond = respond
        self.poll_delay = poll_delay
        self.duration_ms = 200
        self.pwm = 60
        self.imu_plan = 'adaptive'
        self.heartbeat_at = clock()
        self.current_gyro_bias_ns = None
        self.last_send_bracket = None
        self.commands = []
        self.events = []
        self.replies = deque()
        self.sequence = 0
        self.sensor_reply = '10,20,30'

    def send(self, command):
        """Record a command and enqueue its synthetic sensor reply if enabled."""
        self.commands.append(dict(command) if isinstance(command, dict) else command)
        stamp = int(self.clock() * 1e9)
        self.last_send_bracket = dict(begin_ns=stamp, complete_ns=stamp)
        if command == '{Heartbeat}':
            self.heartbeat_at = self.clock()
            return None
        self.sequence += 1
        tag = f't{self.sequence}'
        if command['N'] in (2, 3) and self.respond:
            self.replies.append('{' + tag + '_' + self.sensor_reply + '}')
        return tag

    def poll(self):
        """Advance the optional delay once and return queued local replies."""
        if self.poll_delay:
            self.clock.now += self.poll_delay
            self.poll_delay = 0.0
        replies = list(self.replies)
        self.replies.clear()
        return replies

    def event(self, kind, **payload):
        """Retain event kind and payload in memory for assertions."""
        self.events.append((kind, payload))

    def command_numbers(self):
        """Return firmware command numbers, excluding heartbeat strings."""
        return [command['N'] for command in self.commands if isinstance(command, dict)]


class DriveLogFailureOwner(FakeOwner):
    """Mimic a logging error after N4 may already have reached the transport."""

    def send(self, command):
        """Record the command, then fail only after a drive transmission."""
        tag = super().send(command)
        if isinstance(command, dict) and command['N'] == 4:
            raise OSError('Drive event log failed after transmission')
        return tag


class MotionSchedulingTests(unittest.TestCase):
    """Verify dispatch refusal, stop priority and retained fault evidence."""

    def test_late_wake_refuses_drive(self):
        """A wake more than 50 ms past scheduled start must never emit N4."""
        clock = FakeClock(skip=(100.98, 101.12))
        owner = FakeOwner(clock)
        sampler = MotionSampler(owner, clock=clock, sleep=clock.sleep)
        with self.assertRaisesRegex(TimeoutError, 'Late motion start'):
            sampler.run(1, False, FakeRecorder([100.85, 100.95]))
        self.assertNotIn(4, owner.command_numbers())
        self.assertEqual(sampler.evidence['status'], 'incomplete')
        self.assertTrue(sampler.evidence['samples'])
        self.assertEqual(owner.events[-1][0], 'motion_telemetry')

    def test_pending_timeout_prevents_due_drive(self):
        """An unanswered pre-roll request takes priority over an on-time N4."""
        clock = FakeClock(skip=(100.7, 101.01))
        owner = FakeOwner(clock, respond=False)
        sampler = MotionSampler(owner, clock=clock, sleep=clock.sleep)
        with self.assertRaisesRegex(TimeoutError, 'IMU response timeout'):
            sampler.run(1, False, FakeRecorder([100.85, 100.95]))
        self.assertNotIn(4, owner.command_numbers())
        self.assertIn('IMU response timeout', sampler.evidence['error'])

    def test_stale_completed_frames_refuse_drive(self):
        """Two completed images older than 500 ms do not authorize dispatch."""
        clock = FakeClock()
        owner = FakeOwner(clock)
        sampler = MotionSampler(owner, clock=clock, sleep=clock.sleep)
        with self.assertRaisesRegex(RuntimeError, 'fresh pre-motion camera'):
            sampler.run(1, False, FakeRecorder([100.0, 100.1]))
        self.assertNotIn(4, owner.command_numbers())

    def test_poll_delay_stops_before_next_sensor(self):
        """Crossing the stop deadline inside poll sends N100 before more N2/N3."""
        clock = FakeClock()
        owner = FakeOwner(clock, poll_delay=0.3)
        sampler = MotionSampler(owner, clock=clock, sleep=clock.sleep)
        stop_seconds, samples = sampler.run(1, False)
        self.assertEqual(owner.command_numbers()[:3], [4, 100, 2])
        self.assertEqual(owner.command_numbers().count(4), 1)
        self.assertAlmostEqual(stop_seconds, 0.3)
        self.assertTrue(samples)
        self.assertEqual(sampler.evidence['status'], 'complete')

    def test_bad_reply_stops_and_retains_fault(self):
        """Malformed active-motion IMU data emits stop and an incomplete record."""
        clock = FakeClock()
        owner = FakeOwner(clock)
        owner.sensor_reply = '10,20'
        sampler = MotionSampler(owner, clock=clock, sleep=clock.sleep)
        with self.assertRaisesRegex(ValueError, 'Malformed motion IMU'):
            sampler.run(1, False)
        self.assertEqual(owner.command_numbers()[-1], 100)
        self.assertEqual(sampler.evidence['status'], 'incomplete')
        self.assertIsNotNone(sampler.evidence['stop_elapsed_ms'])
        self.assertIn('Malformed motion IMU', owner.events[-1][1]['error'])

    def test_bias_age_is_rechecked_at_dispatch(self):
        """A bias older than ten seconds refuses N4 at the actual dispatch gate."""
        clock = FakeClock()
        owner = FakeOwner(clock)
        owner.current_gyro_bias_ns = 89_000_000_000
        sampler = MotionSampler(owner, clock=clock, sleep=clock.sleep)
        with self.assertRaisesRegex(TimeoutError, 'Gyro bias older than 10 s'):
            sampler.run(1, False)
        self.assertNotIn(4, owner.command_numbers())

    def test_drive_log_failure_still_attempts_stop(self):
        """An N4 send failure after transmission must still attempt N100."""
        clock = FakeClock()
        owner = DriveLogFailureOwner(clock)
        sampler = MotionSampler(owner, clock=clock, sleep=clock.sleep)
        with self.assertRaisesRegex(OSError, 'Drive event log failed'):
            sampler.run(1, False)
        self.assertEqual(owner.command_numbers(), [4, 100])
        self.assertEqual(sampler.evidence['status'], 'incomplete')
        self.assertIsNotNone(sampler.evidence['stop_elapsed_ms'])


if __name__ == '__main__':
    unittest.main()
