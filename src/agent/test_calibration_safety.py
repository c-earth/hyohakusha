"""Verify the user-defined battery cutoff without connecting to hardware.

No CLI inputs. unittest prints pass/fail results and returns a process status.
Probe requests/replies are local test values in estimated volts.
"""

import unittest

from calibration_session import CalibrationSession


class BatteryProbe(CalibrationSession):
    """Replace network/log operations with recorded commands for battery tests.

Constructor input is voltage float in V. commands stores command dictionaries;
no socket is created and no hardware/file output occurs.
"""

    def __init__(self, voltage):
        """Store voltage float and empty command list; no return value."""
        self.voltage = voltage
        self.commands = []

    def request(self, command):
        """Accept N1 dictionary and return voltage string; no network activity."""
        if command != {'N': 1}:
            raise AssertionError('Expected battery request')
        return str(self.voltage)

    def send(self, command):
        """Record command dictionary and return None; no network activity."""
        self.commands.append(command)

    def event(self, kind, **payload):
        """Accept event string/payload without output; return None."""
        pass


class BatterySafetyTests(unittest.TestCase):
    """Test cutoff boundary and stop ordering with no inputs or hardware output."""

    def test_below_threshold_stops(self):
        """Verify 6.999 V sends N100 before raising; no inputs/return value."""
        probe = BatteryProbe(6.999)
        with self.assertRaises(RuntimeError):
            probe.battery()
        self.assertEqual(probe.commands, [{'N': 100}])

    def test_boundary_and_above(self):
        """Verify 7.0/7.857 V do not trigger cutoff; no inputs/return value."""
        for voltage in (7.0, 7.857):
            with self.subTest(voltage=voltage):
                probe = BatteryProbe(voltage)
                self.assertEqual(probe.battery(), voltage)
                self.assertEqual(probe.commands, [])

    def test_nonfinite_stops(self):
        """Verify nonfinite values send N100 then raise; no inputs/return value."""
        for voltage in (float('nan'), float('inf')):
            with self.subTest(voltage=voltage):
                probe = BatteryProbe(voltage)
                with self.assertRaises(RuntimeError):
                    probe.battery()
                self.assertEqual(probe.commands, [{'N': 100}])


if __name__ == '__main__':
    unittest.main()
