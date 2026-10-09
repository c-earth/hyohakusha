"""Run bounded rover calibration with a single TCP owner.

CLI inputs: session timestamp/name, IP address and explicit safe-area assumption.
Outputs: UTC JSONL commands/replies, JPEGs, manifest and provenance under data.
Trials use PWM 60/80, positive 100/200 ms expiry and optional half-duration stop.
No metric geometry, stopping distance or autonomous clearance is inferred.
"""

import argparse
import hashlib
import json
import math
import select
import socket
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import cv2

from gyro_bias import GyroBiasCalibrator
from timed_camera import TimedCameraRecorder


class CalibrationSession:
    """Own TCP, bounded trial sequencing and evidence files.

Constructor inputs: argparse namespace with session/name/address and safe-area
flag. Attributes hold one socket, receive buffer, sequence and output paths.
Methods produce files and send rover commands; measurements remain native units.
"""

    def __init__(self, args):
        """Validate input and create session evidence folders; returns None."""
        if not args.safe_area_assumed:
            raise ValueError('Explicit safe-area assumption required')
        datetime.strptime(args.session, '%Y%m%d%H%M%S%f')
        if len(args.session) != 17 or not args.name.strip():
            raise ValueError('Invalid session metadata')
        self.root = Path(__file__).resolve().parents[2]
        session = self.root / 'data' / args.session
        info = session / 'info.txt'
        if session.exists() and (not info.exists() or info.read_text(encoding='utf-8-sig').strip() != args.name):
            raise ValueError('Session metadata mismatch')
        session.mkdir(exist_ok=True)
        if not info.exists():
            info.write_text(args.name + '\n', encoding='utf-8')
        datetime.strptime(args.run_stamp, '%Y%m%d%H%M%S%f')
        if len(args.run_stamp) != 17:
            raise ValueError('Invalid New York run timestamp')
        stamp = args.run_stamp
        self.logs = session / 'logs' / stamp
        self.captures = session / 'captures' / stamp
        self.logs.mkdir(parents=True)
        self.captures.mkdir(parents=True)
        for folder in (self.logs, self.captures):
            (folder / 'info.txt').write_text('Bounded calibration; safe area assumed by user; native units.\n', encoding='utf-8')
        self.address = args.address
        self.duration_ms = args.duration_ms
        self.pwm = args.pwm
        self.drive_only = bool(args.drive_only)
        self.battery_only = bool(args.battery_only)
        self.gyro_only = bool(args.gyro_only)
        self.timed_camera = bool(args.timed_camera)
        self.repeats = args.repeats
        self.imu_plan = args.imu_plan
        self.turn_only = bool(args.turn_only)
        self.sock = None
        self.buffer = ''
        self.sequence = 0
        self.heartbeat_at = 0.0
        self.trials = []
        self.frames = []

    def event(self, kind, **payload):
        """Append event kind and arbitrary payload with UTC/monotonic times; no return."""
        item = dict(utc=datetime.now(timezone.utc).isoformat(), monotonic_ns=time.monotonic_ns(), kind=kind, payload=payload)
        with (self.logs / 'events.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(item) + '\n')

    def send(self, command):
        """Send allowed command dictionary or heartbeat string; return unique tag or None."""
        tag = None
        if isinstance(command, dict):
            command = dict(command)
            if command['N'] not in (1, 2, 3, 4, 5, 6, 7, 8, 100):
                raise ValueError('Unsupported command')
            if command['N'] == 4 and (command['T'] not in (100, 200) or command['D2'] not in (60, 80) or command['D1'] not in (1, 2, 3, 4)):
                raise ValueError('Drive outside fixed calibration bounds')
            self.sequence += 1
            tag = f'c{self.sequence}'
            command['H'] = tag
            message = json.dumps(command, separators=(',', ':'))
        else:
            if command != '{Heartbeat}':
                raise ValueError('Invalid raw message')
            message = command
        self.sock.sendall(message.encode('ascii'))
        if message == '{Heartbeat}':
            self.heartbeat_at = time.monotonic()
        self.event('send', message=message)
        return tag

    def poll(self):
        """Read ready TCP data and log complete brace frames; return list of strings."""
        replies = []
        if select.select([self.sock], [], [], 0)[0]:
            data = self.sock.recv(4096)
            if not data:
                raise ConnectionError('Peer closed')
            self.buffer += data.decode('ascii', errors='strict')
            if len(self.buffer) > 8192:
                raise ValueError('Receive buffer overflow')
            while '}' in self.buffer:
                end = self.buffer.index('}') + 1
                frame, self.buffer = self.buffer[:end], self.buffer[end:]
                start = frame.find('{')
                if start >= 0:
                    frame = frame[start:]
                    self.event('receive', message=frame)
                    replies.append(frame)
        return replies

    def wait(self, seconds):
        """Maintain heartbeat and receive logging for nonnegative seconds; no return."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if time.monotonic() - self.heartbeat_at >= 0.4:
                self.send('{Heartbeat}')
                self.heartbeat_at = time.monotonic()
            self.poll()
            time.sleep(0.002)

    def request(self, command):
        """Send stationary command dictionary; return matching reply within 2 s."""
        tag = self.send(command)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            for frame in self.poll():
                prefix = '{' + tag + '_'
                if frame.startswith(prefix):
                    return frame[len(prefix):-1]
            if time.monotonic() - self.heartbeat_at >= 0.4:
                self.send('{Heartbeat}')
                self.heartbeat_at = time.monotonic()
            time.sleep(0.002)
        raise TimeoutError(f'No reply for {tag}')

    def sensors(self):
        """Read stopped N1/N2/N3/N7/N8; return validated native-unit dictionary."""
        values = {}
        values['battery_v'] = self.battery()
        for number, name in ((2, 'gyro'), (3, 'accel')):
            vector = [int(value) for value in self.request(dict(N=number)).split(',')]
            if len(vector) != 3 or any(value < -32768 or value > 32767 for value in vector):
                raise ValueError('Invalid IMU vector')
            values[name] = vector
        values['echo_us'] = int(self.request(dict(N=7, D1=2, T=30000)))
        if not 0 < values['echo_us'] <= 30000:
            raise ValueError('Unknown/invalid echo')
        values['floor'] = [int(self.request(dict(N=8, D1=index))) for index in range(3)]
        if any(value < 0 or value > 1023 for value in values['floor']):
            raise ValueError('Invalid floor ADC')
        self.event('sensors', **values)
        return values

    def battery(self):
        """Read N1 estimate in V; return float or stop/raise on invalid or <7 V.

        No inputs. The 7.0 V stop threshold is explicitly user-provided; battery
        conversion accuracy is unverified. Exactly 7.0 V does not trigger it.
        """
        voltage = float(self.request(dict(N=1)))
        self.event('battery', voltage_v=voltage, stop_below_v=7.0)
        if not math.isfinite(voltage) or voltage < 7.0:
            self.send(dict(N=100))
            self.event('battery_stop', voltage_v=voltage, threshold_v=7.0)
            raise RuntimeError('Invalid battery reading or battery below 7.0 V: stopped')
        return voltage

    def capture(self, label):
        """Capture stopped JPEG for string label, validate decoding; return filename."""
        name = f'{len(self.frames):04d}-{label}.jpg'
        begin = datetime.now(timezone.utc).isoformat()
        self.send('{Heartbeat}')
        with urllib.request.urlopen(f'http://{self.address}/capture', timeout=1.5) as response:
            data = response.read(2_000_001)
        if len(data) > 2_000_000:
            raise ValueError('Oversize capture')
        path = self.captures / name
        path.write_bytes(data)
        if cv2.imread(str(path)) is None:
            raise ValueError('Undecodable JPEG')
        item = dict(file=name, request_utc=begin, received_utc=datetime.now(timezone.utc).isoformat())
        self.frames.append(item)
        self.event('capture', **item)
        self.send('{Heartbeat}')
        return name

    def run(self):
        """Execute configured bounded trials, optional pan, or stopped-only checks.

        No inputs; configuration comes from attributes. Returns None and writes
        evidence files. Always attempts N100 and TCP close, including faults.
        """
        try:
            self.sock = socket.create_connection((self.address, 100), timeout=2)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.sock.settimeout(0.05)
            self.event('start', safe_area='user assumption', source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       imu_plan=self.imu_plan, timed_camera=self.timed_camera, repeats=self.repeats,
                       pwm=self.pwm, duration_ms=self.duration_ms)
            self.send(dict(N=100))
            self.wait(0.5)
            if self.battery_only:
                voltage = self.battery()
                self.event('battery_check_complete', voltage_v=voltage, movement=False)
                print(f'Battery: {voltage:.3f} V; stop threshold <7.0 V', flush=True)
                return
            if self.gyro_only:
                self.battery()
                bias = self.calibrate_gyro()
                self.event('gyro_calibration_complete', **bias)
                print(f"Fresh gyro bias (raw XYZ): {bias['bias_raw_xyz']}", flush=True)
                return
            baseline = [self.sensors() for _ in range(12)]
            self.event('baseline', samples=baseline)
            self.capture('baseline')
            for repeat in range(0 if self.drive_only else 3):
                for angle in (100, 95, 100, 105, 100):
                    if self.request(dict(N=5, D1=1, D2=angle)) != 'ok':
                        raise ValueError('Pan failed')
                    self.wait(0.65)
                    self.capture(f'pan-{repeat}-{angle}')
                for step in (1, -1, 5, -5):
                    if self.request(dict(N=6, D1=step)) != 'ok':
                        raise ValueError('Increment failed')
                    self.wait(0.65)
                    self.capture(f'step-{repeat}-{step}')
            self.send(dict(N=100))
            for repeat in range(self.repeats):
                for direction, number in self.directions():
                    for early in self.stop_modes():
                        before = self.sensors()
                        bias = self.calibrate_gyro()
                        first = self.capture(f'{repeat}-{direction}-{early}-before')
                        self.battery()
                        if time.monotonic_ns()-bias['monotonic_ns'] > 10_000_000_000:
                            raise TimeoutError('Gyro bias older than 10 s: movement refused')
                        self.send('{Heartbeat}')
                        recorder = None
                        if self.timed_camera:
                            recorder = TimedCameraRecorder(self.address, self.captures/f'trial-{len(self.trials):03d}-timed')
                            recorder.start()
                        try:
                            stop_elapsed, telemetry = self.motion(number, early, recorder)
                        except Exception:
                            self.send(dict(N=100))
                            raise
                        finally:
                            if recorder is not None:
                                recorder.close()
                        if recorder is not None and recorder.error:
                            raise RuntimeError(f'Camera recording failed: {recorder.error}')
                        after = self.sensors()
                        second = self.capture(f'{repeat}-{direction}-{early}-after')
                        later = self.capture(f'{repeat}-{direction}-{early}-settled')
                        trial = dict(repeat=repeat, direction=direction, early_stop=early, pwm=self.pwm, duration_ms=self.duration_ms,
                                     host_stop_elapsed_ms=stop_elapsed*1000, before=before, after=after,
                                     first=first, second=second, later=later, gyro_telemetry=telemetry, gyro_bias=bias,
                                     timed_frames=recorder.frames if recorder else [],
                                     timed_folder=recorder.folder.name if recorder else None, imu_plan=self.imu_plan)
                        self.trials.append(trial)
                        self.event('trial', **trial)
                        print(f'Trial {len(self.trials)} {direction} early={early}', flush=True)
            self.event('complete', trials=len(self.trials), baseline=baseline, physical_stop_latency_verified=False)
        except Exception as error:
            self.event('failure', error=str(error))
            raise
        finally:
            if self.sock is not None:
                try:
                    self.send(dict(N=100))
                    self.wait(0.2)
                except Exception as error:
                    self.event('cleanup_failure', error=str(error))
                self.sock.close()
            (self.logs / 'trials.json').write_text(json.dumps(self.trials, indent=2), encoding='utf-8')
            (self.captures / 'frames.json').write_text(json.dumps(self.frames, indent=2), encoding='utf-8')
            print(f'Logs: {self.logs}\nCaptures: {self.captures}', flush=True)

    def directions(self):
        """Return calibration direction/name pairs; no inputs or hardware action."""
        return (('left', 1), ('right', 2)) if self.turn_only else (('forward', 3), ('backward', 4), ('left', 1), ('right', 2))

    def stop_modes(self):
        """Return expiry/early-stop booleans; no inputs or hardware action."""
        return (False, True)

    def calibrate_gyro(self):
        """Attempt up to three stopped bias checks without relaxing their gates.

        No inputs. Returns first accepted fresh bias dictionary, logging every
        rejected attempt. No wheel commands. Persistent rejection raises ValueError.
        """
        for attempt in range(3):
            try:
                return self.measure_gyro_bias()
            except ValueError as error:
                self.event('gyro_bias_rejected', attempt=attempt, reason=str(error))
                self.send(dict(N=100))
        raise ValueError('Three stationary bias checks rejected: movement refused')

    def measure_gyro_bias(self):
        """Refresh host gyro bias while stopped; return guarded bias dictionary.

        No inputs. Sends N100, waits 0.7 s, brackets five gyro/accel reads with
        camera frames and checks visual/IMU stability. Rejects uncertain evidence.
        Logs inputs and accepted bias; never updates firmware calibration.
        """
        self.send(dict(N=100))
        self.wait(0.7)
        first = self.capture(f'bias-{self.sequence}-before')
        gyro, accel = [], []
        for _ in range(5):
            for number, destination in ((2, gyro), (3, accel)):
                vector = [int(value) for value in self.request(dict(N=number)).split(',')]
                if len(vector) != 3 or any(value < -32768 or value > 32767 for value in vector):
                    raise ValueError('Invalid bias-calibration IMU vector')
                destination.append(vector)
            self.wait(0.05)
        second = self.capture(f'bias-{self.sequence}-after')
        calibrator = GyroBiasCalibrator()
        visual = calibrator.image_motion(cv2.imread(str(self.captures/first)), cv2.imread(str(self.captures/second)))
        self.event('gyro_bias_evidence', gyro=gyro, accel=accel, first=first, second=second, visual=visual)
        bias = calibrator.estimate(gyro, accel, visual)
        bias['monotonic_ns'] = time.monotonic_ns()
        bias['frames'] = [first, second]
        self.event('gyro_bias_accepted', **bias)
        return bias

    def motion(self, direction, early, recorder=None):
        """Run direction int with expiry/early stop and asynchronous IMU reads.

        early is bool. Return host N100 elapsed seconds and timestamped raw XYZ
        gyro/accel replies through 1 s after N100. At most one outstanding request;
        poll never waits for a reply before checking stop deadline. Firmware
        response tag is global, so sensing may retag expiry acknowledgments.
        Sampling/serial handling can perturb firmware timing; no angle conversion.
        Optional recorder is HTTP-only. With it, IMU starts 1 s before scheduled
        N4 and runs 1.6 s beyond stop; require two pre-motion camera frames.
        gyro-focus/adaptive turn sampling favors N2 until 300 ms beyond stop,
        leaving sparse in-motion acceleration; returned times use scheduled N4
        epoch. Actual N4 send offset is logged separately.
        """
        self.send('{Heartbeat}')
        start = time.monotonic() + (1.0 if recorder is not None else 0)
        if recorder is not None:
            recorder.epoch_ns = int(start*1e9)
        driven = False
        drive_send_ms = None
        stop_at = start + (self.duration_ms / 2000 if early else self.duration_ms / 1000 + 0.05)
        finish = stop_at + (1.6 if recorder is not None else 1.0)
        stopped = False
        stop_elapsed = 0.0
        pending = None
        pending_number = 2
        next_number = 2
        requested = 0.0
        next_sample = time.monotonic()
        samples = []
        while time.monotonic() < finish:
            now = time.monotonic()
            if recorder is not None and recorder.error:
                self.send(dict(N=100))
                raise RuntimeError(f'Camera fault: {recorder.error}')
            if not driven and now >= start:
                if recorder is not None and len(recorder.frames) < 2:
                    raise RuntimeError('Insufficient pre-motion camera frames: drive refused')
                self.send(dict(N=4, D1=direction, D2=self.pwm, T=self.duration_ms))
                drive_send_ms = (time.monotonic()-start)*1000
                driven = True
            if not stopped and now >= stop_at:
                self.send(dict(N=100))
                stop_elapsed = time.monotonic() - start
                stopped = True
            if now - self.heartbeat_at >= 0.4:
                self.send('{Heartbeat}')
                self.heartbeat_at = now
            for frame in self.poll():
                if pending and frame.startswith('{' + pending + '_'):
                    content = frame[len(pending)+2:-1]
                    if content != 'ok':
                        vector = [int(value) for value in content.split(',')]
                        if len(vector) != 3 or any(value < -32768 or value > 32767 for value in vector):
                            raise ValueError('Malformed motion gyro')
                        samples.append(dict(sensor='gyro' if pending_number == 2 else 'accel', request_ms=(requested-start)*1000, received_ms=(time.monotonic()-start)*1000, xyz=vector))
                        pending = None
            if pending and now-requested > 0.75:
                raise TimeoutError('Motion gyro response timeout')
            if pending is None and now >= next_sample:
                requested = time.monotonic()
                pending_number = next_number
                focus = self.imu_plan == 'gyro-focus' or (self.imu_plan == 'adaptive' and direction in (1, 2))
                if focus and start-0.05 <= requested <= stop_at+0.3:
                    pending_number = 2
                pending = self.send(dict(N=pending_number))
                next_number = 3 if next_number == 2 else 2
                next_sample = requested + 0.04
            time.sleep(0.002)
        if not stopped:
            self.send(dict(N=100))
        self.event('motion_telemetry', samples=samples, stop_elapsed_ms=stop_elapsed*1000, drive_send_ms=drive_send_ms,
                   pre_roll=recorder is not None)
        return stop_elapsed, samples


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--address', default='192.168.4.1')
    parser.add_argument('--run-stamp', required=True)
    parser.add_argument('--duration-ms', type=int, choices=(100, 200), default=100)
    parser.add_argument('--pwm', type=int, choices=(60, 80), default=60)
    parser.add_argument('--drive-only', type=int, choices=(0, 1), default=0)
    parser.add_argument('--battery-only', type=int, choices=(0, 1), default=0)
    parser.add_argument('--gyro-only', type=int, choices=(0, 1), default=0)
    parser.add_argument('--timed-camera', type=int, choices=(0, 1), default=0)
    parser.add_argument('--repeats', type=int, choices=(1, 2, 3), default=3)
    parser.add_argument('--imu-plan', choices=('alternate', 'gyro-focus', 'adaptive'), default='adaptive')
    parser.add_argument('--turn-only', type=int, choices=(0, 1), default=0)
    parser.add_argument('--safe-area-assumed', action='store_true')
    CalibrationSession(parser.parse_args()).run()
