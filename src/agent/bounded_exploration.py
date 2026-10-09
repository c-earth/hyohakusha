"""Collect three bounded forward exploration observations in assumed-safe area.

CLI inputs: session/name/run timestamp/IP and explicit safe-area assumption.
Outputs: calibration-compatible logs, images and relative observation records.
PWM60, three T200 ms pulses only; no reverse, turn or power escalation. This is
a local data-collection pilot, not autonomous room search or validated odometry.
"""

import argparse
import json

from calibration_session import CalibrationSession


class BoundedExplorationSession(CalibrationSession):
    """Reuse one-owner calibration checks for a fixed three-step forward pilot.

Constructor input: argparse namespace with session metadata/safe-area flag.
No claimed metric pose/clearance. Reject >20% shortening of raw echo relative to
previous stopped observation as a provisional change gate, not collision braking.
Fresh bias/camera/IMU and N1<7 V cutoff are retained before/after each short pulse.
"""

    def __init__(self, args):
        """Fix motion/recording bounds and initialize parent owner; no return."""
        args.duration_ms, args.pwm, args.repeats = 200, 60, 3
        args.drive_only, args.timed_camera = 1, 1
        args.battery_only, args.gyro_only = 0, 0
        args.imu_plan, args.turn_only = 'alternate', 0
        super().__init__(args)
        self.previous_echo = None
        self.forward_commands = 0
        self.event('bounded_exploration_scope', forward_pulses=3, pwm=60, duration_ms=200,
                   total_commanded_duration_ms=600, area='user-assumed safe calibration area', metric_pose=False)

    def directions(self):
        """Return forward-only direction tuple; no inputs/hardware action."""
        return (('forward', 3),)

    def stop_modes(self):
        """Return expiry-only mode; no inputs/hardware action."""
        return (False,)

    def sensors(self):
        """Return parent sensor batch or stop on >20% shortening of prior echo.

        No inputs. Echo is raw us; the ratio is a conservative observed-change
        trigger, not calibrated obstacle distance or swept-body clearance.
        """
        values = super().sensors()
        if self.previous_echo is not None and values['echo_us'] < 0.8*self.previous_echo:
            self.send(dict(N=100))
            self.event('echo_change_stop', previous_us=self.previous_echo, current_us=values['echo_us'])
            raise RuntimeError('Raw echo shortened >20%: stop and reassess')
        self.previous_echo = values['echo_us']
        return values

    def send(self, command):
        """Send parent command after enforcing three forward N4 limit; return tag."""
        if isinstance(command, dict) and command.get('N') == 4:
            if command.get('D1') != 3 or command.get('D2') != 60 or command.get('T') != 200 or self.forward_commands >= 3:
                raise ValueError('Exploration pilot movement bounds exceeded')
            self.forward_commands += 1
        return super().send(command)

    def run(self):
        """Run fixed pilot and save observation-only map, including faults; no return."""
        try:
            super().run()
        finally:
            observations = [dict(index=index, before=trial['first'], after=trial['second'],
                                 echo_before_us=trial['before']['echo_us'], echo_after_us=trial['after']['echo_us'],
                                 metric_position=None, free_space_verified=False)
                            for index, trial in enumerate(self.trials)]
            (self.logs/'observations.json').write_text(json.dumps(dict(observations=observations,
                                                                    commanded_pulses=self.forward_commands,
                                                                    localization_validated=False), indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--run-stamp', required=True)
    parser.add_argument('--address', default='192.168.4.1')
    parser.add_argument('--safe-area-assumed', action='store_true')
    BoundedExplorationSession(parser.parse_args()).run()
