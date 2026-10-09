"""Verify forward stop-comparison scope without files or hardware connections."""

import unittest
from argparse import Namespace
from unittest.mock import patch

from src.agent.runtime.calibration_session import CalibrationSession


class ForwardCalibrationTests(unittest.TestCase):
    """Check direction restrictions and rejection before evidence creation."""

    def test_forward_plan_has_only_two_stop_modes(self):
        """One repeat produces forward expiry and forward early-stop trials."""
        session = object.__new__(CalibrationSession)
        session.forward_only, session.turn_only, session.repeats = True, False, 1
        self.assertEqual(list(session.trial_plan()),
                         [(0, 'forward', 3, False), (0, 'forward', 3, True)])

    def test_default_and_turn_plans_preserved(self):
        """The omitted option preserves original all-direction and turn plans."""
        session = object.__new__(CalibrationSession)
        session.forward_only, session.turn_only = False, False
        self.assertEqual(session.directions(),
                         (('forward', 3), ('backward', 4), ('left', 1), ('right', 2)))
        session.turn_only = True
        self.assertEqual(session.directions(), (('left', 1), ('right', 2)))

    def test_conflict_rejected_before_files_or_connection(self):
        """Mutually exclusive options fail even before session metadata access."""
        with patch('src.agent.runtime.calibration_session.Path.mkdir') as mkdir:
            with patch('src.control.connection.RoverConnection.__init__') as connection:
                with self.assertRaisesRegex(ValueError, 'cannot be combined'):
                    CalibrationSession(Namespace(turn_only=1, forward_only=1))
                mkdir.assert_not_called()
                connection.assert_not_called()
