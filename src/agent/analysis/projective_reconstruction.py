"""Attempt two-view projective structure from saved static pixel matches.

Inputs are a correspondence CSV and new output directory. Canonical cameras
follow Hartley/Zisserman section 9.5; coordinates have arbitrary projective gauge,
not metric shape, distance or pose. Planar-dominated evidence is refused.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


class ProjectiveDiagnostic:
    """Fit unique correspondences and retain diagnostics even on refusal."""

    @staticmethod
    def canonical(f):
        """Return rank-three canonical cameras for rank-two fundamental F."""
        _, _, vt = np.linalg.svd(f.T)
        e = vt[-1]
        cross = np.array([[0, -e[2], e[1]], [e[2], 0, -e[0]], [-e[1], e[0], 0]])
        return np.c_[np.eye(3), np.zeros(3)], np.c_[cross @ f, e]

    @staticmethod
    def fit(a, b):
        """Reject insufficient/planar points; report F and H support in pixels."""
        if len(a) < 16:
            raise ValueError('Fewer than 16 unique static correspondences')
        cv2.setRNGSeed(0)
        h, hm = cv2.findHomography(a, b, cv2.RANSAC, 3.0)
        cv2.setRNGSeed(0)
        f, fm = cv2.findFundamentalMat(a, b, cv2.FM_RANSAC, 1.0, .99)
        if f is None or f.shape != (3, 3) or fm is None:
            raise ValueError('No fundamental model')
        valid = fm.ravel().astype(bool)
        outside = valid & ~hm.ravel().astype(bool) if hm is not None else valid
        details = dict(unique_matches=len(a), f_inliers=int(valid.sum()),
                       h_inliers=int(hm.sum()) if hm is not None else None,
                       f_inliers_outside_h=int(outside.sum()),
                       f_singular_values=np.linalg.svd(f, compute_uv=False).tolist())
        if valid.sum() < 12 or outside.sum() < 4:
            raise ValueError('Insufficient nonhomographic support: ' + json.dumps(details))
        return f, valid, details

    def run(self, source, output, max_x):
        """Exclude moving right region in both views, deduplicate, save result."""
        output.mkdir(parents=True, exist_ok=False)
        rows = list(csv.DictReader(source.open()))
        points = np.array([[float(r[k]) for k in ('x1_px', 'y1_px', 'x2_px', 'y2_px')] for r in rows])
        points = points[(points[:, 0] < max_x) & (points[:, 2] < max_x)]
        _, unique = np.unique(np.round(points, 2), axis=0, return_index=True)
        points = points[np.sort(unique)]
        a, b = points[:, :2], points[:, 2:]
        result = dict(status='refused', source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      source=str(source.resolve()), max_x_both_views_px=max_x,
                      limitation='Arbitrary projective gauge distorts Euclidean shape; no metric room model.',
                      reference='https://www.robots.ox.ac.uk/~vgg/hzbook/hzbook2/HZepipolar.pdf')
        manifest = source.parent.parent / 'provenance.json'
        if manifest.exists():
            result['image_source_provenance'] = json.loads(manifest.read_text())
            result['image_manifest_sha256'] = hashlib.sha256(manifest.read_bytes()).hexdigest()
        try:
            f, valid, details = self.fit(a, b)
            p, q = self.canonical(f)
            cloud = cv2.triangulatePoints(p, q, a[valid].T, b[valid].T).T
            finite = np.abs(cloud[:, 3]) > 1e-9
            cloud = cloud[finite] / cloud[finite, 3:4]
            errors = []
            for camera, observed in ((p, a[valid][finite]), (q, b[valid][finite])):
                projected = cloud @ camera.T
                errors.append(np.linalg.norm(projected[:, :2]/projected[:, 2:3] - observed, axis=1))
            keep = np.isfinite(cloud).all(axis=1) & (np.maximum(*errors) < 2)
            # Perturbations test epipolar prediction stability, not gauge-dependent 3D distances.
            rng = np.random.default_rng(0)
            sensitivity = []
            for _ in range(10):
                fp, _ = cv2.findFundamentalMat(a + rng.normal(0, .5, a.shape), b + rng.normal(0, .5, b.shape), cv2.FM_8POINT)
                if fp is not None:
                    ph, qh = np.c_[a, np.ones(len(a))], np.c_[b, np.ones(len(b))]
                    lines = ph @ fp.T
                    sensitivity.append(float(np.median(np.abs((qh*lines).sum(axis=1))/np.maximum(np.linalg.norm(lines[:, :2], axis=1), 1e-12))))
            result.update(details, status='diagnostic_only', cameras=[p.tolist(), q.tolist()],
                          finite_points=int(finite.sum()), retained_points=int(keep.sum()),
                          perturbation_half_px_epipolar_medians=sensitivity,
                          reprojection_medians_px=[float(np.median(x)) for x in errors])
            cv2.setRNGSeed(0)
            held_f, _ = cv2.findFundamentalMat(a[::2], b[::2], cv2.FM_RANSAC, 1.0, .99)
            if held_f is not None and held_f.shape == (3, 3):
                ph, qh = np.c_[a[1::2], np.ones(len(a[1::2]))], np.c_[b[1::2], np.ones(len(b[1::2]))]
                lines = ph @ held_f.T
                errors_h = np.abs((qh*lines).sum(axis=1))/np.maximum(np.linalg.norm(lines[:, :2], axis=1), 1e-12)
                result['unique_alternating_heldout_epipolar_median_px'] = float(np.median(errors_h))
                result['heldout_limit'] = 'Unique match holdout only; spatial independence and third view absent.'
            with (output/'projective.ply').open('w') as handle:
                handle.write(f'ply\nformat ascii 1.0\ncomment arbitrary projective gauge\nelement vertex {keep.sum()}\nproperty float x\nproperty float y\nproperty float z\nend_header\n')
                for xyz in cloud[keep, :3]:
                    handle.write(' '.join(map(str, xyz))+'\n')
        except ValueError as error:
            result['reason'] = str(error)
        (output/'diagnostics.json').write_text(json.dumps(result, indent=2))
        heldout = result.get('unique_alternating_heldout_epipolar_median_px')
        (output/'report.md').write_text('# Projective diagnostic\n\n'+result['status']+'\n\n'+result.get('reason', 'Two-view fit only; third-view validation absent.')+'\n\n'+f'Unique-match alternating holdout median point-to-epipolar-line error: {heldout} px. This differs from square-root Sampson error. Low fitted reprojection is not independent validation.\n\n'+result['limitation']+'\n')
        print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matches', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-x', type=float, required=True)
    args = parser.parse_args()
    ProjectiveDiagnostic().run(args.matches, args.output, args.max_x)
