"""Verify third-view transfer independently on synthetic camera projections."""

import unittest

import numpy as np

from src.agent.analysis.projective_third_view import ThirdViewCheck


class ThirdCameraTests(unittest.TestCase):
    """Known synthetic camera supplies held-out transfer truth."""

    def test_heldout_projection(self):
        """DLT trained on half the points predicts unseen points accurately."""
        rng = np.random.default_rng(44)
        x = rng.uniform(-1, 1, (30, 3)) + [0, 0, 5]
        truth = np.array([[400., 20., 300., 100.], [0., 400., 200., -20.], [0., 0., 1., .2]])
        projected = np.c_[x, np.ones(len(x))] @ truth.T
        uv = projected[:, :2]/projected[:, 2:]
        fitted, _ = ThirdViewCheck.camera(x[::2], uv[::2])
        predicted = np.c_[x[1::2], np.ones(15)] @ fitted.T
        self.assertTrue(np.allclose(predicted[:, :2]/predicted[:, 2:], uv[1::2], atol=1e-7))

    def test_planar_training_refused(self):
        """Coplanar 3D data cannot determine a full third camera."""
        x = np.c_[np.random.default_rng(44).normal(size=(12, 2)), np.ones(12)]
        with self.assertRaises(ValueError):
            ThirdViewCheck.camera(x, x[:, :2])
