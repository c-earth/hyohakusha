"""Verify numerical IMU integration against analytical inputs, without hardware.

No CLI inputs. unittest emits test results/process status. Tests cover known
rotation, irregular sampling, gravity compensation and invalid timestamps.
"""

import unittest

import numpy as np
from scipy.spatial.transform import Rotation

from src.agent.analysis.inertial import InertialIntegrator


class IntegrationTests(unittest.TestCase):
    """Analytical checks for integration; no inputs or hardware/file output."""

    def test_constant_acceleration_irregular_times(self):
        """2 m/s² for 2 s gives 4 m/s and 4 m; no inputs/return value."""
        times = np.array([0, 0.2, 0.9, 2.0])
        first, second = InertialIntegrator.cumulative(times, np.tile([2, 0, 0], (4, 1)))
        np.testing.assert_allclose(first[-1], [4, 0, 0])
        np.testing.assert_allclose(second[-1], [4, 0, 0])

    def test_linearly_increasing_acceleration(self):
        """a(t)=t for 3 s gives v=4.5, x=4.5; no inputs/return value."""
        times = np.array([0, 0.4, 1.9, 3.0])
        values = np.column_stack([times, np.zeros((4, 2))])
        velocity, position = InertialIntegrator.cumulative(times, values)
        self.assertAlmostEqual(velocity[-1, 0], 4.5)
        self.assertAlmostEqual(position[-1, 0], 4.5)

    def test_bias_and_gravity_at_rest(self):
        """Constant biased rest must not accumulate motion; no inputs/return value."""
        times = np.linspace(0, 2, 21)
        gyro_bias = [-350, 50, 250]
        reference = [100, -80, 15300]
        trace = InertialIntegrator().integrate(times, np.tile(gyro_bias, (21, 1)), times,
                                              np.tile(reference, (21, 1)), gyro_bias, reference)
        np.testing.assert_allclose(trace['yaw_deg_nominal'], 0, atol=1e-12)
        np.testing.assert_allclose(trace['velocity_increment_m_s_nominal'], 0, atol=1e-12)
        np.testing.assert_allclose(trace['displacement_m_nominal_zero_initial_velocity'], 0, atol=1e-12)

    def test_rotation_compensates_gravity(self):
        """Known 90° roll in 1 s with gravity only yields zero translation.

        No inputs/return value. Generated sensor vectors follow the analytical
        rotation, testing frame convention and nominal scale conversion.
        """
        times = np.linspace(0, 1, 101)
        rotations = Rotation.from_euler('x', (90*times)[:, None], degrees=True)
        gravity_sensor = rotations.inv().apply(np.tile([0, 0, 16384], (101, 1)))
        trace = InertialIntegrator().integrate(times, np.tile([90*131, 0, 0], (101, 1)),
                                              times, gravity_sensor, [0, 0, 0], [0, 0, 16384])
        final = Rotation.from_quat(trace['orientation_quaternion_xyzw'][-1])
        np.testing.assert_allclose(final.apply([0, 0, 1]), [0, -1, 0], atol=1e-10)
        np.testing.assert_allclose(trace['velocity_increment_m_s_nominal'][-1], 0, atol=1e-10)

    def test_missing_support_not_extrapolated(self):
        """Output starts at overlapping sample support, not t=0; no inputs/return."""
        gyro_times, accel_times = [0.1, 0.5, 1], [0.2, 0.4, 0.8]
        trace = InertialIntegrator().integrate(gyro_times, np.zeros((3, 3)), accel_times,
                                              np.tile([0, 0, 16384], (3, 1)), [0, 0, 0], [0, 0, 16384])
        self.assertEqual(trace['time_s'][0], 0.2)
        self.assertEqual(trace['time_s'][-1], 0.8)

    def test_bad_timestamps_rejected(self):
        """Duplicated/reversed times must fail; no inputs/return value."""
        for times in ([0, 0], [1, 0]):
            with self.assertRaises(ValueError):
                InertialIntegrator.cumulative(times, np.zeros((2, 3)))

    def test_full_gyro_turn_does_not_depend_on_accel_window(self):
        """Full two-second 10 deg/s gyro support gives 20 nominal degrees."""
        integrator = InertialIntegrator()
        gt = np.array([0, 0.3, 1.1, 2.0])
        gyro = np.tile([0, 0, 1310], (4, 1))
        full = integrator.yaw_trace(gt, gyro, [0, 0, 0])
        overlap = integrator.integrate(gt, gyro, [0.5, 1.0],
                                       np.tile([0, 0, 16384], (2, 1)),
                                       [0, 0, 0], [0, 0, 16384])
        self.assertAlmostEqual(full['gyro_z_integral_deg_nominal'][-1], 20)
        self.assertAlmostEqual(overlap['yaw_deg_nominal'][-1], 10)

    def test_slow_yaw_keeps_small_increments_and_positive_sign(self):
        """Small increments survive bias removal without legacy deadband."""
        times = np.linspace(5, 6, 101)
        gyro = np.tile([0, 0, 300+13.1], (101, 1))
        trace = InertialIntegrator().yaw_trace(times, gyro, [0, 0, 300])
        self.assertEqual(trace['gyro_z_integral_deg_nominal'][0], 0)
        self.assertAlmostEqual(trace['gyro_z_integral_deg_nominal'][-1], 0.1)


if __name__ == '__main__':
    unittest.main()
