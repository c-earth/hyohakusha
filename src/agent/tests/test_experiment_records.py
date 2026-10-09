"""Verify fault records and cleanup using temporary files and fake transports.

The fixtures bypass session construction and replace every operation that could
contact hardware. Temporary directories contain only synthetic test evidence.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.agent.runtime.calibration_session import CalibrationSession
from src.control.connection import RoverConnection
from src.control.timed_camera import TimedCameraRecorder


class TrialProbe(CalibrationSession):
    """Supply one successful pre-read and a failing post-read without hardware.

    folder is a temporary Path. logs/captures contain test evidence only;
    commands and events retain fake writes in memory. No socket is constructed.
    """

    def __init__(self, folder):
        """Initialize the minimal acquisition state in a temporary directory."""
        self.logs = folder / 'logs'
        self.captures = folder / 'captures'
        self.logs.mkdir()
        self.captures.mkdir()
        self.trials = []
        self.frames = []
        self.commands = []
        self.events = []
        self.pwm = 60
        self.duration_ms = 200
        self.imu_plan = 'adaptive'
        self.timed_camera = False
        self.current_gyro_bias_ns = None
        self.sensor_reads = 0

    def sensors(self):
        """Return synthetic pre-motion values, then fail the post-motion read."""
        self.sensor_reads += 1
        if self.sensor_reads > 1:
            raise OSError('Post-motion sensor failure')
        return dict(battery_v=7.6, gyro=[10, 20, 30], accel=[0, 0, 16384],
                    echo_us=10000, floor=[100, 100, 100])

    def calibrate_gyro(self):
        """Return a known fresh synthetic bias at one monotonic second."""
        return dict(monotonic_ns=1_000_000_000, bias_raw_xyz=[10, 20, 30],
                    accel_reference_raw_xyz=[0, 0, 16384])

    def capture(self, label):
        """Return a synthetic relative JPEG name for the supplied trial label."""
        return label + '.jpg'

    def battery(self):
        """Return a synthetic 7.6 V reading without a network request."""
        return 7.6

    def send(self, command):
        """Record a fake command dictionary without a transport."""
        self.commands.append(dict(command))
        return 'fake'

    def event(self, kind, **payload):
        """Retain event payloads in memory, including partial trial status."""
        self.events.append((kind, payload))


class CompletedSampler:
    """Return a synthetic completed pulse for a later sensor-failure scenario.

    owner is the TrialProbe; evidence mirrors the sampler's externally consumed
    fields, with one retained gyro observation and host stop at 250 ms.
    """

    def __init__(self, owner):
        """Store the fake owner and initialize fixed completed evidence."""
        self.owner = owner
        self.evidence = dict(status='complete', drive_send_ms=0.0,
                             stop_elapsed_ms=250.0,
                             samples=[dict(sensor='gyro', request_ms=20.0,
                                           received_ms=25.0, xyz=[10, 20, 100])])

    def run(self, direction, early, recorder=None):
        """Record the synthetic pulse and return host stop seconds and samples."""
        self.owner.send(dict(N=4, D1=direction, D2=60, T=200))
        return 0.25, self.evidence['samples']


class RecordedSocket:
    """Expose only close state; this fixture never creates a network socket."""

    def __init__(self):
        """Initialize the local closed flag to False."""
        self.closed = False

    def close(self):
        """Mark the local socket substitute closed."""
        self.closed = True


class CleanupProbe(CalibrationSession):
    """Observe cleanup ordering with optional stop and logging failures.

    sock is a local RecordedSocket. fail defaults to True to reject both N100
    and logging; events retain the actual socket state when logging was tried.
    """

    def __init__(self, sock, fail=True):
        """Store fake transport state and command, wait and event attempts."""
        RoverConnection.__init__(self, 'unused.invalid')
        self.sock = sock
        self.recorded_socket = sock
        self.fail = fail
        self.commands = []
        self.waits = []
        self.event_kinds = []
        self.events = []

    def send(self, command):
        """Record the stop attempt and optionally raise a transport failure."""
        self.commands.append(dict(command))
        if self.fail:
            raise OSError('N100 transport unavailable')

    def wait(self, seconds):
        """Record requested cleanup wait seconds without sleeping or polling."""
        self.waits.append(seconds)

    def event(self, kind, **payload):
        """Record event-time close state and optionally raise a disk failure."""
        self.event_kinds.append(kind)
        self.events.append(dict(kind=kind, payload=payload,
                                socket_was_closed=self.recorded_socket.closed,
                                owner_released_socket=self.sock is None))
        if self.fail:
            raise OSError('Event log unavailable')


class TimedSocket:
    """Advance a probe's synthetic nanoseconds while recording local I/O.

    owner is a TransportProbe. sendall takes 20 ms and recv takes 30 ms; neither
    uses a real socket. received bytes contain two complete synthetic frames.
    """

    def __init__(self, owner):
        """Store the clock-owning probe and outgoing byte list."""
        self.owner = owner
        self.messages = []

    def sendall(self, data):
        """Record bytes and advance the synthetic transport duration by 20 ms."""
        self.messages.append(data)
        self.owner.now_ns += 20_000_000

    def recv(self, size):
        """Return bounded synthetic frames after advancing the clock by 30 ms."""
        self.owner.now_ns += 30_000_000
        return b'{c1_1,2,3}{c2_4,5,6}'[:size]


class TransportProbe(CalibrationSession):
    """Use real send/poll parsing with fake I/O and a slow in-memory logger.

    now_ns starts at one second. Each event simulates a 500 ms logging delay;
    transport timestamps must describe I/O before that delay occurs.
    """

    def __init__(self):
        """Initialize a fake socket, clock, protocol state and event list."""
        RoverConnection.__init__(self, 'unused.invalid')
        self.now_ns = 1_000_000_000
        self.sock = TimedSocket(self)
        self.sequence = 0
        self.buffer = ''
        self.last_send_bracket = None
        self.last_receive_ns = None
        self.events = []

    def clock_ns(self):
        """Return synthetic monotonic nanoseconds without advancing."""
        return self.now_ns

    def event(self, kind, **payload):
        """Retain event fields and simulate 500 ms of logging overhead."""
        self.events.append((kind, payload))
        self.now_ns += 500_000_000


class UnfinishedWorker:
    """Mimic an HTTP worker that remains alive after the bounded join."""

    def __init__(self):
        """Initialize the recorded join timeout in seconds."""
        self.join_timeout = None

    def join(self, timeout):
        """Record timeout seconds without waiting or starting any thread."""
        self.join_timeout = timeout

    def is_alive(self):
        """Report the synthetic unfinished worker state."""
        return True


class ExperimentRecordTests(unittest.TestCase):
    """Ensure failed acquisition remains visible and cleanup is independent."""

    def test_post_motion_fault_preserves_partial_trial(self):
        """A post-pulse read failure retains command context and collected IMU."""
        with tempfile.TemporaryDirectory() as folder:
            probe = TrialProbe(Path(folder))
            with patch('src.agent.runtime.calibration_session.MotionSampler', CompletedSampler), \
                    patch('src.agent.runtime.calibration_session.time.monotonic_ns', return_value=1_000_000_000):
                with self.assertRaisesRegex(OSError, 'Post-motion sensor failure'):
                    probe.acquire_trial(0, 'left', 1, False)
            stored = json.loads((probe.logs / 'trials.json').read_text(encoding='utf-8'))
            self.assertEqual(stored, probe.trials)
            self.assertEqual(len(stored), 1)
            trial = stored[0]
            self.assertEqual(trial['status'], 'incomplete')
            self.assertEqual(trial['motion']['status'], 'complete')
            self.assertEqual(trial['host_stop_elapsed_ms'], 250.0)
            self.assertEqual(trial['gyro_telemetry'][0]['xyz'], [10, 20, 100])
            self.assertEqual(trial['direction'], 'left')
            self.assertIn('Post-motion sensor failure', trial['error'])
            self.assertNotIn('after', trial)
            self.assertEqual(probe.commands[-1], {'N': 100})
            self.assertEqual(probe.events[-1][0], 'trial')

    def test_stop_and_log_failure_still_close_socket(self):
        """Failure to send N100 and write its error cannot prevent TCP close."""
        sock = RecordedSocket()
        probe = CleanupProbe(sock)
        with patch('builtins.print'):
            probe.close()
        self.assertTrue(sock.closed)
        self.assertIsNone(probe.sock)
        self.assertEqual(probe.commands, [{'N': 100}])
        self.assertEqual(probe.event_kinds, ['cleanup_failure', 'cleanup'])

    def test_successful_cleanup_is_recorded_after_socket_close(self):
        """A positive cleanup event must observe a closed, released socket."""
        sock = RecordedSocket()
        probe = CleanupProbe(sock, fail=False)
        probe.close()
        self.assertEqual(probe.commands, [{'N': 100}])
        self.assertEqual(probe.waits, [0.2])
        self.assertEqual(probe.event_kinds, ['cleanup'])
        event = probe.events[0]
        self.assertTrue(event['socket_was_closed'])
        self.assertTrue(event['owner_released_socket'])
        self.assertTrue(event['payload']['socket_closed'])
        self.assertIsNone(event['payload']['stop_error'])
        self.assertFalse(event['payload']['physical_rest_verified'])

    def test_transport_timestamps_exclude_event_log_delay(self):
        """Send brackets and shared batch receipt time precede slow logging."""
        probe = TransportProbe()
        with patch('src.control.connection.time.monotonic_ns', side_effect=probe.clock_ns), \
                patch('src.control.connection.select.select', return_value=([probe.sock], [], [])):
            tag = probe.send({'N': 2})
            frames = probe.poll()
        self.assertEqual(tag, 'c1')
        self.assertEqual(probe.last_send_bracket, dict(begin_ns=1_000_000_000, complete_ns=1_020_000_000))
        self.assertEqual(frames, ['{c1_1,2,3}', '{c2_4,5,6}'])
        self.assertEqual(probe.last_receive_ns, 1_550_000_000)
        receipts = [payload['received_ns'] for kind, payload in probe.events if kind == 'receive']
        self.assertEqual(receipts, [1_550_000_000, 1_550_000_000])
        self.assertEqual(probe.now_ns, 2_550_000_000)

    def test_camera_join_failure_preserves_detached_manifest(self):
        """Late worker mutations cannot alter already-returned frame evidence."""
        with tempfile.TemporaryDirectory() as folder:
            recorder = TimedCameraRecorder('unused.invalid', Path(folder) / 'frames')
            recorder.worker = UnfinishedWorker()
            recorder.epoch_ns = 1_000_000_000
            recorder.frames.append(dict(file='frame-0.jpg', request_ns=1_010_000_000,
                                        received_ns=1_020_000_000))
            frames = recorder.close()
            stored = json.loads((recorder.folder / 'frames.json').read_text(encoding='utf-8'))
            recorder.frames[0]['file'] = 'late-change.jpg'
            recorder.frames.append(dict(file='late-frame.jpg'))
            self.assertTrue(recorder.stop_event.is_set())
            self.assertFalse(stored['worker_joined'])
            self.assertIn('did not finish', stored['error'])
            self.assertEqual(stored['frames'], frames)
            self.assertEqual(len(frames), 1)
            self.assertEqual(frames[0]['file'], 'frame-0.jpg')
            self.assertEqual(frames[0]['request_ms'], 10.0)
            self.assertEqual(frames[0]['received_ms'], 20.0)
            self.assertNotIn('request_ms', recorder.frames[0])


if __name__ == '__main__':
    unittest.main()
