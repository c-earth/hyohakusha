"""Test stationary gyro-bias evidence gates without hardware.

No CLI inputs. unittest prints pass/fail results. Test arrays are numerical
fixtures; no rover movement, simulation, file output or connection occurs.
"""

import unittest

import cv2
import numpy as np

from src.agent.runtime.gyro_bias import GyroBiasCalibrator


class GyroBiasTests(unittest.TestCase):
    """Test bias means and rejection of motion/insufficient evidence; no inputs."""

    def test_stationary_mean(self):
        """Recover known raw bias from five quiet samples; no inputs/return value."""
        gyro = np.tile([-350, 50, 250], (5, 1))
        accel = np.tile([0, 0, 15300], (5, 1))
        result = GyroBiasCalibrator().estimate(gyro, accel, dict(tracks=30, median_px=0.3, p95_px=0.8))
        self.assertEqual(result['bias_raw_xyz'], [-350, 50, 250])
        self.assertFalse(result['physical_rest_proven'])

    def test_steady_rotation_visual_rejected(self):
        """Constant gyro rate must not become bias when images move; no return."""
        with self.assertRaises(ValueError):
            GyroBiasCalibrator().estimate(np.tile([0, 0, 5000], (5, 1)), np.tile([0, 0, 15300], (5, 1)),
                                          dict(tracks=40, median_px=8, p95_px=10))

    def test_acceleration_variation_rejected(self):
        """Reject changing acceleration despite quiet image summary; no return."""
        accel = np.tile([0, 0, 15300], (5, 1))
        accel[-1, 0] = 2000
        with self.assertRaises(ValueError):
            GyroBiasCalibrator().estimate(np.zeros((5, 3)), accel, dict(tracks=30, median_px=0.2, p95_px=0.5))

    def test_missing_visual_texture_rejected(self):
        """Featureless images provide insufficient rest evidence; no return."""
        with self.assertRaises(ValueError):
            GyroBiasCalibrator.image_motion(np.zeros((80, 80, 3), np.uint8), np.zeros((80, 80, 3), np.uint8))

    def test_coherent_camera_translation_rejected(self):
        """A four-pixel global shift must fail rest gate; no inputs/return."""
        gray = np.random.default_rng(41).integers(30, 220, size=(180, 240), dtype=np.uint8)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        first = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        second = cv2.warpAffine(first, np.float32([[1, 0, 4], [0, 1, 0]]), (240, 180))
        motion = GyroBiasCalibrator.image_motion(first, second)
        self.assertGreater(motion['median_px'], 3)
        with self.assertRaises(ValueError):
            GyroBiasCalibrator().estimate(np.zeros((5, 3)), np.tile([0, 0, 15300], (5, 1)), motion)

    def test_small_corrupted_patch_does_not_move_background(self):
        """Reject local tracking outliers while preserving broad quiet support."""
        gray = np.random.default_rng(42).integers(30, 220, size=(180, 240), dtype=np.uint8)
        first = cv2.cvtColor(cv2.GaussianBlur(gray, (3, 3), 0), cv2.COLOR_GRAY2BGR)
        second = first.copy()
        second[20:45, 20:45] = 255
        motion = GyroBiasCalibrator.image_motion(first, second)
        self.assertGreaterEqual(motion['coherent_fraction'], 0.7)
        self.assertLess(motion['median_px'], 0.2)


if __name__ == '__main__':
    unittest.main()
