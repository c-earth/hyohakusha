"""Check canonical epipolar invariance and planar correspondence refusal."""

import unittest

import numpy as np

from src.agent.analysis.projective_reconstruction import ProjectiveDiagnostic


class ProjectiveTests(unittest.TestCase):
    """Synthetic geometry provides independent algebraic constraints."""

    def test_canonical_projection_satisfies_epipolar_constraint(self):
        """A rank-two F and reconstructed cameras agree on arbitrary points."""
        f = np.array([[0., -1., 2.], [1., 0., -3.], [-2., 3., 0.]])
        p, q = ProjectiveDiagnostic.canonical(f)
        self.assertEqual(np.linalg.matrix_rank(q), 3)
        rng = np.random.default_rng(42)
        points = np.c_[rng.normal(size=(20, 3)), np.ones(20)]
        a, b = points @ p.T, points @ q.T
        self.assertTrue(np.allclose(np.sum((a @ f.T)*b, axis=1), 0))

    def test_planar_correspondences_refused(self):
        """Perfect translation homography cannot support nonplanar geometry."""
        a = np.random.default_rng(42).uniform(20, 600, (40, 2))
        with self.assertRaises(ValueError):
            ProjectiveDiagnostic.fit(a, a + [8, 3])
