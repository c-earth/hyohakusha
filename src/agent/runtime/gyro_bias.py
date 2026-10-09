"""Estimate gyro bias from stationary evidence without operating hardware.

Inputs to class methods: repeated raw IMU vectors and stopped camera frames.
Outputs: bias/noise summaries or rejection. Provisional image/noise thresholds
are evidence gates, not proof of physical rest or a calibrated sensor scale.
"""

from datetime import datetime, timezone

import cv2
import numpy as np


class GyroBiasCalibrator:
    """Estimate a fresh three-axis raw gyro bias only with stationary evidence.

    No constructor inputs. Limits: >=5 IMU samples, gyro std <=50 counts per
    axis, accel std <=300 counts per axis, >=20 valid visual tracks, median
    motion <=1 px and 95th percentile <=3 px. These are provisional thresholds
    based on prior quiet observations, not validated absolute rest criteria.
    Visual tracks must support a coherent robust transform with >=70% inliers
    spanning >=25% of image width/height; raw outlier statistics are retained.
    """

    @staticmethod
    def image_motion(first, second):
        """Return optical-flow motion summary for two decoded BGR images.

        Inputs: matching nonempty image arrays. Output: valid track count and
        median/95th percentile pixel motion. Reject insufficient visual evidence;
        forward/backward tracking filters ambiguous matches without hardware.
        Robust partial-affine support rejects inconsistent tracking outliers;
        retain raw statistics and reject small-area/minority support.
        """
        if first is None or second is None or first.shape != second.shape:
            raise ValueError('Invalid stationary camera pair')
        gray1, gray2 = [cv2.cvtColor(value, cv2.COLOR_BGR2GRAY) for value in (first, second)]
        points = cv2.goodFeaturesToTrack(gray1, maxCorners=300, qualityLevel=0.02, minDistance=8)
        if points is None or len(points) < 20:
            raise ValueError('Insufficient stationary image texture')
        moved, valid, _ = cv2.calcOpticalFlowPyrLK(gray1, gray2, points, None)
        if moved is None:
            raise ValueError('Stationary optical flow failed')
        returned, backward, _ = cv2.calcOpticalFlowPyrLK(gray2, gray1, moved, None)
        if returned is None:
            raise ValueError('Backward stationary optical flow failed')
        keep = (valid.ravel() != 0) & (backward.ravel() != 0) & (np.linalg.norm((returned-points)[:, 0], axis=1) <= 1)
        original, target = points[keep, 0], moved[keep, 0]
        raw_delta = np.linalg.norm(target-original, axis=1)
        if len(raw_delta) < 20:
            raise ValueError('Insufficient valid stationary tracks')
        cv2.setRNGSeed(0)
        transform, inliers = cv2.estimateAffinePartial2D(original, target, method=cv2.RANSAC,
                                                        ransacReprojThreshold=1.0, confidence=0.99)
        if transform is None or inliers is None:
            raise ValueError('No coherent stationary visual motion model')
        support = inliers.ravel().astype(bool)
        if np.mean(support) < 0.7:
            raise ValueError('Too many inconsistent stationary visual tracks')
        span = np.ptp(original[support], axis=0)
        if span[0] < gray1.shape[1]*0.25 or span[1] < gray1.shape[0]*0.25:
            raise ValueError('Stationary visual evidence covers too little of the image')
        delta = raw_delta[support]
        if len(delta) < 20:
            raise ValueError('Insufficient valid stationary tracks')
        return dict(tracks=int(len(delta)), median_px=float(np.median(delta)), p95_px=float(np.percentile(delta, 95)),
                    raw_median_px=float(np.median(raw_delta)), raw_p95_px=float(np.percentile(raw_delta, 95)),
                    coherent_fraction=float(np.mean(support)), visual_transform=transform.tolist())

    def estimate(self, gyro, accel, image_motion):
        """Return timestamped raw bias from repeated vectors and image summary.

        gyro/accel are >=5 Nx3 signed-count samples. image_motion is output from
        image_motion(). Reject motion/invalid evidence; bias is arithmetic mean
        in raw counts, without firmware changes or degree/s conversion.
        """
        gyro, accel = np.asarray(gyro, float), np.asarray(accel, float)
        if gyro.ndim != 2 or gyro.shape[1] != 3 or gyro.shape != accel.shape or len(gyro) < 5 or not np.all(np.isfinite(gyro)) or not np.all(np.isfinite(accel)):
            raise ValueError('At least five finite paired IMU vectors required')
        if np.any(gyro < -32768) or np.any(gyro > 32767) or np.any(accel < -32768) or np.any(accel > 32767):
            raise ValueError('Invalid signed raw counts')
        gyro_std, accel_std = np.std(gyro, axis=0), np.std(accel, axis=0)
        if np.any(gyro_std > 50) or np.any(accel_std > 300):
            raise ValueError('IMU varies too much for bias calibration')
        if image_motion['tracks'] < 20 or not np.isfinite(image_motion['median_px']) or not np.isfinite(image_motion['p95_px']) or image_motion['median_px'] > 1 or image_motion['p95_px'] > 3:
            raise ValueError('Camera does not support stationary bias calibration')
        return dict(utc=datetime.now(timezone.utc).isoformat(), bias_raw_xyz=np.mean(gyro, axis=0).tolist(),
                    gyro_std_raw_xyz=gyro_std.tolist(), accel_reference_raw_xyz=np.mean(accel, axis=0).tolist(),
                    accel_std_raw_xyz=accel_std.tolist(), samples=len(gyro), image_motion=image_motion,
                    physical_rest_proven=False)
