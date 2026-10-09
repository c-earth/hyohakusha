"""Collect a bounded exploration segment with calibration evidence at each step.

CLI inputs: session/name/run timestamp/IP and explicit safe-area assumption.
Outputs: calibration-compatible logs, images and relative observation records.
Default: three forward PWM60/T200 pulses. An explicit plan may contain one to
three forward/left/right pulses under the same limits. No reverse or power
escalation; no autonomous route selection, metric pose or validated odometry.
"""

import argparse
import json

from .calibration_session import CalibrationSession


class BoundedExplorationSession(CalibrationSession):
    """Reuse calibration checks for at most three predetermined short actions.

Constructor input: argparse namespace with session metadata/safe-area flag.
No claimed metric pose/clearance. Reject >90% shortening of raw echo while
heading is unchanged. Turn observations start a new echo reference, since
different pointing directions do not measure approach to the same obstacle.
Fresh bias/camera/IMU and N1<7 V cutoff are retained before/after each short pulse.
"""

    def __init__(self, args):
        """Fix motion/recording bounds and initialize parent owner; no return."""
        requested_actions = getattr(args, 'actions', None)
        self.actions = tuple(('forward',) * 3 if requested_actions is None else requested_actions)
        if not 1 <= len(self.actions) <= 3 or any(action not in ('forward', 'left', 'right') for action in self.actions):
            raise ValueError('Exploration requires 1-3 forward/left/right actions')
        args.duration_ms, args.pwm, args.repeats = 200, 60, len(self.actions)
        args.drive_only, args.timed_camera = 1, 1
        args.battery_only, args.gyro_only = 0, 0
        args.imu_plan, args.turn_only = 'adaptive', 0
        super().__init__(args)
        self.previous_echo = None
        self.compare_echo = True
        self.forward_commands = 0
        self.movement_commands = 0
        self.event('bounded_exploration_scope', actions=self.actions,
                   forward_pulses=self.actions.count('forward'), pwm=60, duration_ms=200,
                   total_commanded_duration_ms=200*len(self.actions),
                   area='user-assumed safe calibration area', metric_pose=False)

    def directions(self):
        """Return the planned action names and firmware direction IDs."""
        numbers = dict(forward=3, left=1, right=2)
        return tuple((name, numbers[name]) for name in self.actions)

    def trial_plan(self):
        """Yield each planned action once, retaining per-step repeat indices."""
        for index, (direction, number) in enumerate(self.directions()):
            yield index, direction, number, False

    def acquire_trial(self, repeat, direction, number, early):
        """Collect one calibration-compatible step, resetting echo after turns."""
        self.compare_echo = direction == 'forward'
        if not self.compare_echo:
            self.previous_echo = None
        super().acquire_trial(repeat, direction, number, early)

    def stop_modes(self):
        """Return expiry-only mode; no inputs/hardware action."""
        return (False,)

    def sensors(self):
        """Return parent sensor batch or stop on >90% shortening of prior echo.

        No inputs. Echo is raw us; the ratio is a user-selected observed-change
        trigger, not calibrated obstacle distance or swept-body clearance.
        """
        values = super().sensors()
        if self.compare_echo and self.previous_echo is not None and values['echo_us'] < 0.1*self.previous_echo:
            self.send(dict(N=100))
            self.event('echo_change_stop', previous_us=self.previous_echo, current_us=values['echo_us'])
            raise RuntimeError('Raw echo shortened >90%: stop and reassess')
        self.previous_echo = values['echo_us']
        return values

    def send(self, command):
        """Allow only the next planned N4 within PWM60/T200 bounds; return tag.

        Count attempted sends conservatively: a transport/log failure may occur
        after transmission. Faults end the segment; they never retry a movement.
        """
        if isinstance(command, dict) and command.get('N') == 4:
            plan = self.directions()
            if self.movement_commands >= len(plan) or command.get('D2') != 60 or command.get('T') != 200:
                raise ValueError('Exploration pilot movement bounds exceeded')
            if command.get('D1') != plan[self.movement_commands][1]:
                raise ValueError('Exploration action differs from the frozen plan')
            self.movement_commands += 1
            if command['D1'] == 3:
                self.forward_commands += 1
        return super().send(command)

    def run(self):
        """Run the frozen segment and save observations, including partial faults."""
        try:
            super().run()
        finally:
            observations = [dict(index=index, status=trial.get('status', 'complete'),
                                 direction=trial.get('direction'),
                                 before=trial.get('first'), after=trial.get('second'),
                                 echo_before_us=trial.get('before', {}).get('echo_us'),
                                 echo_after_us=trial.get('after', {}).get('echo_us'),
                                 metric_position=None, free_space_verified=False)
                            for index, trial in enumerate(self.trials)]
            (self.logs/'observations.json').write_text(json.dumps(dict(observations=observations,
                                                                    actions=self.actions,
                                                                    commanded_pulses=self.movement_commands,
                                                                    forward_pulses=self.forward_commands,
                                                                    localization_validated=False), indent=2), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--run-stamp', required=True)
    parser.add_argument('--address', default='192.168.4.1')
    parser.add_argument('--actions', nargs='+', choices=('forward', 'left', 'right'),
                        help='One to three sequential PWM60/T200 actions; default: three forward')
    parser.add_argument('--safe-area-assumed', action='store_true')
    BoundedExplorationSession(parser.parse_args()).run()
