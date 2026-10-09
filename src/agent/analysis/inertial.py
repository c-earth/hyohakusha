"""Numerical IMU diagnostics using nominal source-configured scales.

The legacy MPU6050_dveGetEulerAngles calculation preserved in UNO backups
motivates bias-corrected Z integration. This implementation uses observed time
support, trapezoids and sensor-positive Z; it omits the legacy interval-dependent
0.05-degree deadband and startup interval. Units remain nominal without live
range/timing verification. No hardware or file I/O occurs in this module.
"""

import numpy as np
from scipy.spatial.transform import Rotation, Slerp


class InertialIntegrator:
    """Integrate orientation and gravity-reference-corrected acceleration.

Constructor inputs: positive gyro counts/(deg/s), accel counts/g, gravity m/s²,
defaulting to 131, 16384 and 9.80665. Initial orientation is identity in sensor
axes, velocity increment and displacement estimate start at zero at window start.
These initial conditions and sensor scales are assumptions, not localization.
"""

    def __init__(self, gyro_scale=131.0, accel_scale=16384.0, gravity=9.80665):
        """Store positive finite conversion factors; no output or hardware action."""
        if not all(np.isfinite(value) and value > 0 for value in (gyro_scale, accel_scale, gravity)):
            raise ValueError('Conversion factors must be positive and finite')
        self.gyro_scale = gyro_scale
        self.accel_factor = gravity / accel_scale

    @staticmethod
    def cumulative(times, values):
        """Integrate Nx3 values over increasing N times in seconds.

        Return cumulative first and second integrals, initially zero. Uses
        piecewise-linear input: trapezoid for first integral and exact linear
        segment formula for second. No extrapolation or zero-velocity reset.
        """
        times, values = np.asarray(times, dtype=float), np.asarray(values, dtype=float)
        if len(times) < 2 or values.shape != (len(times), 3) or not np.all(np.isfinite(times)) or not np.all(np.isfinite(values)) or np.any(np.diff(times) <= 0):
            raise ValueError('Need finite Nx3 samples and strictly increasing times')
        first, second = np.zeros_like(values), np.zeros_like(values)
        for index, dt in enumerate(np.diff(times), start=1):
            first[index] = first[index-1] + dt*(values[index-1]+values[index])/2
            second[index] = second[index-1] + first[index-1]*dt + dt*dt*(2*values[index-1]+values[index])/6
        return first, second

    def integrate(self, gyro_times, gyro_raw, accel_times, accel_raw, gyro_bias, stationary_accel):
        """Return integrated traces over common observed support.

        Times are seconds, raw arrays Nx3 counts, bias/reference are length-3
        stationary counts. Gyro bias is subtracted; rotation matrices integrate
        body angular velocity. Rotate acceleration into the initial sensor frame
        before subtracting the stationary reference vector (gravity plus bias).
        Return JSON-compatible traces, conditional degree/m/s/m estimates and
        raw-count integrals. Missing startup intervals are never extrapolated.
        """
        gt, at = np.asarray(gyro_times, float), np.asarray(accel_times, float)
        gr, ar = np.asarray(gyro_raw, float), np.asarray(accel_raw, float)
        gb, reference = np.asarray(gyro_bias, float), np.asarray(stationary_accel, float)
        if gb.shape != (3,) or reference.shape != (3,) or not np.all(np.isfinite(gb)) or not np.all(np.isfinite(reference)):
            raise ValueError('Finite three-axis bias/reference required')
        raw_angles, _ = self.cumulative(gt, gr-gb)
        self.cumulative(at, ar-reference)
        rates = np.deg2rad((gr-gb)/self.gyro_scale)
        orientation = [Rotation.identity()]
        for index, dt in enumerate(np.diff(gt), start=1):
            orientation.append(orientation[-1] * Rotation.from_rotvec((rates[index-1]+rates[index])*dt/2))
        start, end = max(gt[0], at[0]), min(gt[-1], at[-1])
        if end <= start:
            raise ValueError('Gyro/accel supports do not overlap')
        times = np.unique(np.r_[start, at[(at > start) & (at < end)], end])
        raw_accel = np.column_stack([np.interp(times, at, ar[:, axis]) for axis in range(3)])
        rotations = Slerp(gt, Rotation.concatenate(orientation))(times)
        world_accel = rotations.apply(raw_accel*self.accel_factor) - reference*self.accel_factor
        velocity, position = self.cumulative(times, world_accel)
        raw_velocity, raw_position = self.cumulative(times, raw_accel-reference)
        yaw = rotations.as_euler('xyz', degrees=True)[:, 2]
        return dict(time_s=times.tolist(), gyro_support_s=[float(gt[0]), float(gt[-1])],
                    accel_support_s=[float(at[0]), float(at[-1])],
                    orientation_quaternion_xyzw=rotations.as_quat().tolist(),
                    yaw_deg_nominal=yaw.tolist(), angular_axis_integral_deg_nominal=(raw_angles/self.gyro_scale).tolist(),
                    gyro_axis_count_seconds=raw_angles.tolist(),
                    acceleration_initial_frame_m_s2_nominal=world_accel.tolist(),
                    velocity_increment_m_s_nominal=velocity.tolist(), displacement_m_nominal_zero_initial_velocity=position.tolist(),
                    sensor_frame_accel_count_seconds=raw_velocity.tolist(), sensor_frame_accel_count_seconds2=raw_position.tolist())


    def yaw_trace(self, gyro_times, gyro_raw, gyro_bias):
        """Integrate bias-corrected sensor Z over the full gyro support.

        Inputs are strictly increasing seconds, Nx3 raw signed counts and a
        finite length-3 stationary bias. Return times and cumulative nominal
        degrees, initially zero at the first sample. Positive raw Z is positive
        angle. This fixed-axis turn diagnostic is not full 3D orientation or an
        absolute heading; it does not require accelerometer support.
        """
        times = np.asarray(gyro_times, dtype=float)
        raw = np.asarray(gyro_raw, dtype=float)
        bias = np.asarray(gyro_bias, dtype=float)
        if bias.shape != (3,) or not np.all(np.isfinite(bias)):
            raise ValueError('Finite three-axis gyro bias required')
        angles, _ = self.cumulative(times, raw-bias)
        return dict(time_s=times.tolist(),
                    gyro_z_integral_deg_nominal=(angles[:, 2]/self.gyro_scale).tolist())

    @staticmethod
    def series(samples, sensor, clock):
        """Return seconds/raw Nx3 arrays for sensor and request/midpoint/receipt clock.

        Inputs: list of logged sample dictionaries, sensor gyro/accel and clock
        string. Midpoint is a timing hypothesis, not an acquisition timestamp.
        """
        selected = [sample for sample in samples if sample.get('sensor', 'gyro') == sensor]
        times = [(sample['request_ms'] if clock == 'request' else sample['received_ms'] if clock == 'receipt'
                  else (sample['request_ms']+sample['received_ms'])/2)/1000 for sample in selected]
        return np.asarray(times), np.asarray([sample['xyz'] for sample in selected])
