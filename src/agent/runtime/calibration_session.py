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
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import cv2

from src.agent.runtime.gyro_bias import GyroBiasCalibrator
from src.control.connection import RoverConnection
from src.control.motion import MotionSampler
from src.control.timed_camera import TimedCameraRecorder


class CalibrationSession(RoverConnection):
    """Apply calibration policy and record evidence using one shared TCP owner.

Constructor inputs: argparse namespace with session/name/address and safe-area
flag. Attributes hold trial settings and output paths; RoverConnection owns TCP state.
Methods produce files and send rover commands; measurements remain native units.
"""

    def __init__(self, args):
        """Validate input and create session evidence folders; returns None."""
        if args.turn_only and getattr(args, 'forward_only', 0):
            raise ValueError('Turn-only and forward-only cannot be combined')
        if not args.safe_area_assumed:
            raise ValueError('Explicit safe-area assumption required')
        datetime.strptime(args.session, '%Y%m%d%H%M%S%f')
        if len(args.session) != 17 or not args.name.strip():
            raise ValueError('Invalid session metadata')
        self.root = Path(__file__).resolve().parents[3]
        session = self.root / 'data' / args.session
        info = session / 'info.txt'
        if session.exists() and (not info.exists() or info.read_text(encoding='utf-8-sig').strip() != args.name):
            raise ValueError('Session metadata mismatch')
        session.mkdir(parents=True, exist_ok=True)
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
        super().__init__(args.address)
        self.duration_ms = args.duration_ms
        self.pwm = args.pwm
        self.drive_only = bool(args.drive_only)
        self.battery_only = bool(args.battery_only)
        self.gyro_only = bool(args.gyro_only)
        self.timed_camera = bool(args.timed_camera)
        self.repeats = args.repeats
        self.imu_plan = args.imu_plan
        self.turn_only = bool(args.turn_only)
        self.forward_only = bool(getattr(args, 'forward_only', 0))
        self.trials = []
        self.frames = []
        self.current_gyro_bias_ns = None

    def event(self, kind, **payload):
        """Append event kind and arbitrary payload with UTC/monotonic times; no return."""
        item = dict(utc=datetime.now(timezone.utc).isoformat(), monotonic_ns=time.monotonic_ns(), kind=kind, payload=payload)
        with (self.logs / 'events.jsonl').open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(item) + '\n')


    def send(self, command):
        """Enforce fixed calibration pulse limits before shared transport sends."""
        if isinstance(command, dict) and command.get('N') == 4:
            if command.get('T') not in (100, 200) or command.get('D2') not in (60, 80) or command.get('D1') not in (1, 2, 3, 4):
                raise ValueError('Drive outside fixed calibration bounds')
        return super().send(command)

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
        """Save a stopped JPEG and optional unverified device time; return name."""
        name = f'{len(self.frames):04d}-{label}.jpg'
        begin = datetime.now(timezone.utc).isoformat()
        self.send('{Heartbeat}')
        with urllib.request.urlopen(f'http://{self.address}/capture', timeout=1.5) as response:
            data = response.read(2_000_001)
            camera_timestamp = response.headers.get('X-Timestamp')
        received_utc = datetime.now(timezone.utc).isoformat()
        if len(data) > 2_000_000:
            raise ValueError('Oversize capture')
        path = self.captures / name
        path.write_bytes(data)
        if cv2.imread(str(path)) is None:
            raise ValueError('Undecodable JPEG')
        item = dict(file=name, request_utc=begin, received_utc=received_utc,
                    camera_timestamp=camera_timestamp)
        self.frames.append(item)
        self.event('capture', **item)
        self.send('{Heartbeat}')
        return name

    def run(self):
        """Acquire the configured experiment, preserving partial trials on faults.

        Configuration is supplied at construction. Writes logs/manifests and
        attempts N100 then closes TCP even when cleanup logging fails.
        """
        try:
            sources = {}
            for folder in ('src/control', 'src/tools', 'src/agent/runtime', 'src/agent/analysis'):
                for path in sorted((self.root/folder).iterdir()):
                    if path.is_file() and path.suffix in ('.py', '.ps1', '.psm1'):
                        sources[path.relative_to(self.root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.connect()
            self.event('start', safe_area='user assumption', source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       source_hashes=sources, imu_plan=self.imu_plan, timed_camera=self.timed_camera,
                       repeats=self.repeats, pwm=self.pwm, duration_ms=self.duration_ms,
                       drive_only=self.drive_only, turn_only=self.turn_only,
                       forward_only=self.forward_only,
                       battery_only=self.battery_only, gyro_only=self.gyro_only,
                       directions=self.directions(), stop_modes=self.stop_modes())
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
            for repeat, direction, number, early in self.trial_plan():
                self.acquire_trial(repeat, direction, number, early)
                print(f'Trial {len(self.trials)} {direction} early={early}', flush=True)
            self.event('complete', trials=len(self.trials), baseline=baseline, physical_stop_latency_verified=False)
        except BaseException as error:
            self.event('failure', error=str(error) or type(error).__name__)
            raise
        finally:
            try:
                self.close()
            finally:
                try:
                    (self.logs/'trials.json').write_text(json.dumps(self.trials, indent=2), encoding='utf-8')
                finally:
                    (self.captures/'frames.json').write_text(json.dumps(self.frames, indent=2), encoding='utf-8')
            print(f'Logs: {self.logs}\nCaptures: {self.captures}', flush=True)


    def acquire_trial(self, repeat, direction, number, early):
        """Acquire one trial and persist its partial evidence on every exit.

        repeat is zero-based; direction is a name and number is firmware D1.
        early requests half-duration N100. Append status before gates or motion,
        then checkpoint trials.json even if post-motion sensors/capture fail.
        """
        trial = dict(repeat=repeat, direction=direction, early_stop=early,
                     pwm=self.pwm, duration_ms=self.duration_ms, status='incomplete',
                     gyro_telemetry=[], timed_frames=[], timed_folder=None, imu_plan=self.imu_plan)
        self.trials.append(trial)
        recorder = None
        sampler = None
        try:
            trial['before'] = self.sensors()
            trial['gyro_bias'] = self.calibrate_gyro()
            self.current_gyro_bias_ns = trial['gyro_bias']['monotonic_ns']
            trial['first'] = self.capture(f'{repeat}-{direction}-{early}-before')
            self.battery()
            if time.monotonic_ns()-self.current_gyro_bias_ns > 10_000_000_000:
                raise TimeoutError('Gyro bias older than 10 s: movement refused')
            if self.timed_camera:
                recorder = TimedCameraRecorder(self.address, self.captures/f'trial-{len(self.trials)-1:03d}-timed')
                trial['timed_folder'] = recorder.folder.name
                recorder.start()
            sampler = MotionSampler(self)
            try:
                stop_elapsed, telemetry = sampler.run(number, early, recorder)
                trial['host_stop_elapsed_ms'] = stop_elapsed*1000
                trial['gyro_telemetry'] = telemetry
            finally:
                trial['motion'] = {key: value for key, value in sampler.evidence.items() if key != 'samples'}
                trial['gyro_telemetry'] = sampler.evidence.get('samples', [])
                if sampler.evidence.get('stop_elapsed_ms') is not None:
                    trial['host_stop_elapsed_ms'] = sampler.evidence['stop_elapsed_ms']
                if recorder is not None:
                    trial['timed_frames'] = recorder.close()
            if recorder is not None and recorder.error:
                raise RuntimeError(f'Camera recording failed: {recorder.error}')
            trial['after'] = self.sensors()
            trial['second'] = self.capture(f'{repeat}-{direction}-{early}-after')
            trial['later'] = self.capture(f'{repeat}-{direction}-{early}-settled')
            trial['status'] = 'complete'
        except BaseException as error:
            trial['error'] = str(error) or type(error).__name__
            try:
                self.send(dict(N=100))
            except Exception as stop_error:
                trial['stop_error'] = str(stop_error)
            raise
        finally:
            (self.logs/'trials.json').write_text(json.dumps(self.trials, indent=2), encoding='utf-8')
            self.event('trial', **trial)

    def directions(self):
        """Return calibration direction/name pairs; no inputs or hardware action."""
        if getattr(self, 'forward_only', False):
            return (('forward', 3),)
        return (('left', 1), ('right', 2)) if self.turn_only else (('forward', 3), ('backward', 4), ('left', 1), ('right', 2))

    def trial_plan(self):
        """Yield repeat, direction, firmware ID and stop mode in fixed order."""
        for repeat in range(self.repeats):
            for direction, number in self.directions():
                for early in self.stop_modes():
                    yield repeat, direction, number, early

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
    parser.add_argument('--forward-only', type=int, choices=(0, 1), default=0)
    parser.add_argument('--safe-area-assumed', action='store_true')
    CalibrationSession(parser.parse_args()).run()
