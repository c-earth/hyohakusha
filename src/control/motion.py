"""Schedule one bounded motion pulse and retain telemetry even on failure.

MotionSampler uses the existing session's TCP transport; it never opens a
connection. All times are host monotonic brackets, not device timestamps.
"""

import time


class MotionSampler:
    """Own a pulse schedule while the supplied session owns all TCP traffic.

    owner provides send/poll/event, last_send_bracket, heartbeat_at, duration_ms,
    pwm and imu_plan. Optional clock/sleep callables support deterministic offline
    tests. Start lateness >50 ms or camera age >500 ms refuses dispatch; these
    host evidence limits are provisional, not physical clearance guarantees.
    """

    MAX_START_LATENESS_S = 0.05
    MAX_CAMERA_AGE_S = 0.5

    def __init__(self, owner, clock=None, sleep=None):
        """Store the TCP owner and monotonic seconds/sleep callables."""
        self.owner = owner
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.evidence = {}

    def run(self, direction, early, recorder=None):
        """Return (host stop elapsed seconds, IMU samples) for one pulse.

        direction is firmware 1..4; early requests N100 at half duration.
        Optional recorder is HTTP-only and supplies frame snapshots. Evidence
        is retained on self and logged on both success and failure.
        """
        owner = self.owner
        start = self.clock() + (1.0 if recorder is not None else 0)
        stop_at = None
        finish = start + owner.duration_ms/1000 + 1.65
        driven = stopped = False
        pending = None
        pending_number = next_number = 2
        requested = next_sample = self.clock()
        samples = []
        self.evidence = dict(samples=samples, pre_roll=recorder is not None,
                             scheduled_start_ns=int(start*1e9), drive_send_ms=None,
                             stop_elapsed_ms=None, status='incomplete')
        if recorder is not None:
            recorder.epoch_ns = int(start*1e9)

        def stop_if_due():
            """Send overdue N100 before any additional polling or commands."""
            nonlocal stopped
            if driven and not stopped and self.clock() >= stop_at:
                owner.send(dict(N=100))
                stopped = True
                bracket = dict(owner.last_send_bracket)
                self.evidence['stop_send_bracket_ns'] = bracket
                self.evidence['stop_elapsed_ms'] = (bracket['complete_ns']/1e9-start)*1000

        try:
            # Drain the final request before returning TCP to stopped sensing.
            # Its existing 0.75 s timeout still bounds a missing reply.
            while self.clock() < finish or pending is not None:
                stop_if_due()
                now = self.clock()
                if pending and now-requested > 0.75:
                    raise TimeoutError('Motion IMU response timeout')
                if recorder is not None and recorder.error:
                    raise RuntimeError(f'Camera fault: {recorder.error}')
                if not driven and now >= start:
                    if now-start > self.MAX_START_LATENESS_S:
                        raise TimeoutError('Late motion start refused')
                    if recorder is not None:
                        frames = recorder.snapshot()
                        ready = [frame for frame in frames if frame['received_ns']/1e9 <= now]
                        if len(ready) < 2 or now-ready[-1]['received_ns']/1e9 > self.MAX_CAMERA_AGE_S:
                            raise RuntimeError('Insufficient fresh pre-motion camera frames')
                    now = self.clock()
                    if now-start > self.MAX_START_LATENESS_S:
                        raise TimeoutError('Late motion start refused')
                    bias_ns = getattr(owner, 'current_gyro_bias_ns', None)
                    if bias_ns is not None and now-bias_ns/1e9 > 10:
                        raise TimeoutError('Gyro bias older than 10 s at dispatch')
                    driven = True
                    # If send or its logging fails, transmission may have begun.
                    # The finally path must attempt N100 even without a reply.
                    owner.send(dict(N=4, D1=direction, D2=owner.pwm, T=owner.duration_ms))
                    bracket = dict(owner.last_send_bracket)
                    sent = bracket['complete_ns']/1e9
                    self.evidence['drive_send_bracket_ns'] = bracket
                    self.evidence['drive_send_ms'] = (sent-start)*1000
                    stop_at = sent + (owner.duration_ms/2000 if early else owner.duration_ms/1000+0.05)
                    finish = stop_at + (1.6 if recorder is not None else 1.0)
                stop_if_due()
                if self.clock()-owner.heartbeat_at >= 0.4:
                    owner.send('{Heartbeat}')
                for frame in owner.poll():
                    stop_if_due()
                    if pending and frame.startswith('{' + pending + '_'):
                        content = frame[len(pending)+2:-1]
                        # Old firmware can retag the N4 expiry acknowledgment.
                        if content != 'ok':
                            vector = [int(value) for value in content.split(',')]
                            if len(vector) != 3 or any(value < -32768 or value > 32767 for value in vector):
                                raise ValueError('Malformed motion IMU vector')
                            received_ns = getattr(owner, 'last_receive_ns', None)
                            received = received_ns/1e9 if received_ns is not None else self.clock()
                            samples.append(dict(sensor='gyro' if pending_number == 2 else 'accel',
                                                request_ms=(requested-start)*1000,
                                                received_ms=(received-start)*1000, xyz=vector))
                            pending = None
                stop_if_due()
                now = self.clock()
                if pending and now-requested > 0.75:
                    raise TimeoutError('Motion IMU response timeout')
                if pending is None and now >= next_sample and now < finish:
                    pending_number = next_number
                    focus = owner.imu_plan == 'gyro-focus' or (owner.imu_plan == 'adaptive' and direction in (1, 2))
                    focus_end = stop_at+0.3 if stop_at is not None else start+owner.duration_ms/1000+0.35
                    if focus and start-0.05 <= now <= focus_end:
                        pending_number = 2
                    pending = owner.send(dict(N=pending_number))
                    requested = owner.last_send_bracket['begin_ns']/1e9
                    next_number = 3 if next_number == 2 else 2
                    next_sample = requested+0.04
                self.sleep(0.002)
            if not driven:
                raise TimeoutError('Motion window elapsed without dispatch')
            self.evidence['status'] = 'complete'
        except BaseException as error:
            self.evidence['error'] = str(error) or type(error).__name__
            raise
        finally:
            if driven and not stopped:
                try:
                    owner.send(dict(N=100))
                    self.evidence['stop_send_bracket_ns'] = dict(owner.last_send_bracket)
                    self.evidence['stop_elapsed_ms'] = (owner.last_send_bracket['complete_ns']/1e9-start)*1000
                except Exception as error:
                    self.evidence['stop_error'] = str(error)
            owner.event('motion_telemetry', **self.evidence)
        return self.evidence['stop_elapsed_ms']/1000, samples
