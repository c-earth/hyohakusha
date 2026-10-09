"""Test projective point transfer into a held-out third image offline.

Correspondence CSVs share the first image. Third camera DLT uses training tracks
only; held-out reprojection tests consistency, never Euclidean accuracy.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from src.agent.analysis.projective_reconstruction import ProjectiveDiagnostic


class ThirdViewCheck:
    """Estimate a projective third camera and report independent track errors."""

    @staticmethod
    def camera(x, uv):
        """Fit normalized DLT camera from six or more finite nonplanar points."""
        if len(x) < 6 or np.linalg.matrix_rank(np.c_[x, np.ones(len(x))]) < 4:
            raise ValueError('Third-camera training needs six nonplanar points')
        center, scale = x.mean(axis=0), x.std(axis=0)
        if np.any(scale < 1e-12):
            raise ValueError('Collapsed projective coordinate axis')
        t = np.eye(4)
        t[:3, :3] = np.diag(1/scale)
        t[:3, 3] = -center/scale
        center2, scale2 = uv.mean(axis=0), uv.std(axis=0)
        if np.any(scale2 < 1e-12):
            raise ValueError('Collapsed third-image coordinates')
        s = np.array([[1/scale2[0], 0, -center2[0]/scale2[0]], [0, 1/scale2[1], -center2[1]/scale2[1]], [0, 0, 1.]])
        xn, un = (np.c_[x, np.ones(len(x))] @ t.T), (np.c_[uv, np.ones(len(uv))] @ s.T)
        rows = []
        for point, pixel in zip(xn, un):
            rows.extend([np.r_[point, np.zeros(4), -pixel[0]*point], np.r_[np.zeros(4), point, -pixel[1]*point]])
        _, singular, vt = np.linalg.svd(rows)
        if np.linalg.matrix_rank(rows) < 11:
            raise ValueError('Third-camera DLT is rank deficient')
        return np.linalg.inv(s) @ vt[-1].reshape(3, 4) @ t, singular

    @staticmethod
    def read(path, max_x):
        """Read and deduplicate match locations, excluding right moving region."""
        with path.open() as handle:
            points = np.array([[float(r[k]) for k in ('x1_px', 'y1_px', 'x2_px', 'y2_px')] for r in csv.DictReader(handle)])
        points = points[(points[:, 0] < max_x) & (points[:, 2] < max_x)]
        _, indices = np.unique(np.round(points, 2), axis=0, return_index=True)
        return points[np.sort(indices)]

    def run(self, pair, third, output, max_x):
        """Join tracks in reference image, train third camera, test other tracks."""
        output.mkdir(parents=True, exist_ok=False)
        result = dict(status='refused', limitations='Projective gauge; no metric accuracy. Alternating unique tracks, not spatially independent.',
                      hashes={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in (pair, third, Path(__file__))})
        try:
            ab, ac = self.read(pair, max_x), self.read(third, max_x)
            f, valid, _ = ProjectiveDiagnostic.fit(ab[:, :2], ab[:, 2:])
            ab = ab[valid]
            p, q = ProjectiveDiagnostic.canonical(f)
            homogeneous = cv2.triangulatePoints(p, q, ab[:, :2].T, ab[:, 2:].T).T
            tracks, pixels, reference, used = [], [], [], set()
            for row, point in zip(ab, homogeneous):
                distances = np.linalg.norm(ac[:, :2]-row[:2], axis=1)
                index = int(np.argmin(distances))
                if distances[index] > .5 or index in used or abs(point[3]) < 1e-9:
                    continue
                used.add(index)
                tracks.append(point[:3]/point[3])
                pixels.append(ac[index, 2:])
                reference.append(row[:2].tolist())
            result['joined_tracks'] = len(tracks)
            if len(tracks) < 12:
                raise ValueError('Fewer than 12 consistent reference tracks: six train/six held-out minimum')
            x, uv = np.array(tracks), np.array(pixels)
            camera, singular = self.camera(x[::2], uv[::2])
            projected = np.c_[x, np.ones(len(x))] @ camera.T
            errors = np.linalg.norm(projected[:, :2]/projected[:, 2:3]-uv, axis=1)
            result.update(status='diagnostic_only', train_n=len(x[::2]), heldout_n=len(x[1::2]),
                          train_median_px=float(np.median(errors[::2])), heldout_median_px=float(np.median(errors[1::2])),
                          heldout_errors_px=errors[1::2].tolist(), reference_pixels=reference,
                          camera=camera.tolist(), dlt_singular_values=singular.tolist())
        except ValueError as error:
            result['reason'] = str(error)
        (output/'diagnostics.json').write_text(json.dumps(result, indent=2))
        (output/'report.md').write_text('# Third-view projective check\n\n'+json.dumps(result, indent=2)+'\n')
        print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair', type=Path, required=True)
    parser.add_argument('--third', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-x', type=float, required=True)
    args = parser.parse_args()
    ThirdViewCheck().run(args.pair, args.third, args.output, args.max_x)
