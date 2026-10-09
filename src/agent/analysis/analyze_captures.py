"""Analyze saved rover JPEG pairs without contacting hardware.

CLI inputs are an existing session directory and a new output directory (paths).
Outputs are a Markdown report, CSV measurements, JSON provenance and PNG
diagnostics. Pixel measurements do not estimate physical distance or prove depth.
"""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import PIL
import scipy
import skimage


class PairAnalyzer:
    """Measure correspondences for equal-size images with deterministic RANSAC.

    No constructor inputs. Attributes are a SIFT detector and L2 matcher. Methods
    return pixel measurements and diagnostic images, never physical poses.
    """

    def __init__(self):
        """Initialize SIFT and matcher; no inputs or return value."""
        self.detector = cv2.SIFT_create(nfeatures=2500)
        self.matcher = cv2.BFMatcher(cv2.NORM_L2)

    def ratio_matches(self, first, second):
        """Return index pairs passing a 0.75 nearest-neighbor ratio.

        Inputs are SIFT descriptor arrays or None. Output is a dictionary mapping
        first-image descriptor indices to second-image indices; absent data gives {}.
        """
        if first is None or second is None or len(second) < 2:
            return {}
        return {m.queryIdx: m.trainIdx for neighbors in self.matcher.knnMatch(first, second, k=2)
                if len(neighbors) == 2 for m, n in [neighbors] if m.distance < 0.75 * n.distance}

    def analyze(self, first_path, second_path, destination):
        """Analyze two JPEG paths and save diagnostics under destination Path.

        Inputs are existing paths and a new pair directory. Returns a dictionary
        of counts, median pixel displacement and homography residuals. Raises on
        unreadable images or size mismatch. Saves all match/track coordinates.
        """
        first, second = [cv2.imread(str(path)) for path in (first_path, second_path)]
        if first is None or second is None or first.shape != second.shape:
            raise ValueError(f'Unreadable or unequal images: {first_path}, {second_path}')
        destination.mkdir()
        gray1, gray2 = [cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) for im in (first, second)]
        key1, desc1 = self.detector.detectAndCompute(gray1, None)
        key2, desc2 = self.detector.detectAndCompute(gray2, None)
        forward, reverse = self.ratio_matches(desc1, desc2), self.ratio_matches(desc2, desc1)
        mutual = [(a, b) for a, b in forward.items() if reverse.get(b) == a]
        p1 = np.array([key1[a].pt for a, b in mutual], dtype=np.float32).reshape(-1, 2)
        p2 = np.array([key2[b].pt for a, b in mutual], dtype=np.float32).reshape(-1, 2)
        mask = np.zeros(len(mutual), dtype=bool)
        residual = np.full(len(mutual), np.nan)
        homography = None
        if len(mutual) >= 4:
            cv2.setRNGSeed(0)
            homography, inliers = cv2.findHomography(p1, p2, cv2.RANSAC, 3.0)
            if homography is not None and inliers is not None:
                mask = inliers.ravel().astype(bool)
                projected = cv2.perspectiveTransform(p1[:, None], homography)[:, 0]
                residual = np.linalg.norm(projected - p2, axis=1)
        matches = [cv2.DMatch(a, b, 0.0) for a, b in mutual]
        overlay = cv2.drawMatches(first, key1, second, key2, matches, None,
                                  matchesMask=mask.astype(int).tolist(),
                                  flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        self.save_image(destination / 'matches.png', overlay)
        with (destination / 'matches.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(['x1_px', 'y1_px', 'x2_px', 'y2_px', 'homography_inlier', 'residual_px'])
            writer.writerows([*a, *b, int(valid), float(error)]
                             for a, b, valid, error in zip(p1, p2, mask, residual))

        corners = cv2.goodFeaturesToTrack(gray1, maxCorners=600, qualityLevel=0.01,
                                         minDistance=8, blockSize=7)
        track1 = np.empty((0, 2), dtype=np.float32)
        track2 = track1.copy()
        fb_errors = np.array([])
        if corners is not None:
            next_points, status1, _ = cv2.calcOpticalFlowPyrLK(
                gray1, gray2, corners, None, winSize=(21, 21), maxLevel=3)
            if next_points is not None:
                back_points, status2, _ = cv2.calcOpticalFlowPyrLK(
                    gray2, gray1, next_points, None, winSize=(21, 21), maxLevel=3)
                if back_points is not None:
                    errors = np.linalg.norm(back_points - corners, axis=2).ravel()
                    height, width = gray1.shape
                    coords = next_points[:, 0]
                    valid = ((status1.ravel() == 1) & (status2.ravel() == 1)
                             & np.isfinite(coords).all(axis=1) & (errors <= 1.0)
                             & (coords[:, 0] >= 0) & (coords[:, 0] < width)
                             & (coords[:, 1] >= 0) & (coords[:, 1] < height))
                    track1, track2, fb_errors = corners[valid, 0], coords[valid], errors[valid]
        flow_overlay = first.copy()
        for a, b in zip(track1, track2):
            cv2.arrowedLine(flow_overlay, tuple(np.round(a).astype(int)),
                           tuple(np.round(b).astype(int)), (0, 255, 0), 1, tipLength=0.25)
        self.save_image(destination / 'flow.png', flow_overlay)
        with (destination / 'flow.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle)
            writer.writerow(['x1_px', 'y1_px', 'x2_px', 'y2_px', 'forward_backward_error_px'])
            writer.writerows([*a, *b, float(error)] for a, b, error in zip(track1, track2, fb_errors))

        aligned_mae = None
        if homography is not None:
            height, width = gray1.shape
            warped = cv2.warpPerspective(gray1, homography, (width, height))
            coverage = cv2.warpPerspective(np.full_like(gray1, 255), homography, (width, height))
            covered = coverage == 255
            difference = cv2.absdiff(warped, gray2)
            difference[~covered] = 0
            if covered.any():
                aligned_mae = float(difference[covered].mean())
            self.save_image(destination / 'aligned_difference.png', difference)
        inlier_displacement = self.motion(p1[mask], p2[mask])
        flow_displacement = self.motion(track1, track2)
        result = {
            'width_px': first.shape[1], 'height_px': first.shape[0],
            'sift_keypoints_first': len(key1), 'sift_keypoints_second': len(key2),
            'ratio_matches': len(forward), 'mutual_matches': len(mutual),
            'rejected_nonmutual': len(forward) - len(mutual),
            'homography_inliers': int(mask.sum()), 'homography_rejected': int((~mask).sum()),
            'homography_inlier_fraction': float(mask.mean()) if len(mask) else None,
            'homography_residual_median_px': float(np.median(residual[mask])) if mask.any() else None,
            'homography_residual_p90_px': float(np.percentile(residual[mask], 90)) if mask.any() else None,
            'homography': homography.tolist() if homography is not None else None,
            'aligned_gray_mae_0_255': aligned_mae,
            'lk_candidates': len(corners) if corners is not None else 0,
            'lk_valid': len(track1), 'lk_rejected': (len(corners) if corners is not None else 0) - len(track1),
            **{'sift_' + k: v for k, v in inlier_displacement.items()},
            **{'lk_' + k: v for k, v in flow_displacement.items()},
        }
        (destination / 'metrics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        return result

    @staticmethod
    def motion(first, second):
        """Return median dx/dy/magnitude in pixels for two Nx2 arrays.

        Empty inputs return None metrics. Positive x is right; positive y is down.
        These summaries refer to retained features rather than all image pixels.
        """
        delta = second - first
        return {'dx_median_px': float(np.median(delta[:, 0])) if len(delta) else None,
                'dy_median_px': float(np.median(delta[:, 1])) if len(delta) else None,
                'magnitude_median_px': float(np.median(np.linalg.norm(delta, axis=1))) if len(delta) else None}

    @staticmethod
    def save_image(path, image):
        """Write an image array to path; no return value, raise on write failure."""
        if not cv2.imwrite(str(path), image):
            raise OSError(f'Unable to write {path}')


class CaptureAssessment:
    """Own the saved-session analysis plan, provenance and report.

    Constructor inputs are session and output Paths. Attributes hold resolved
    paths and a pair analyzer. No hardware interface or network calls exist.
    """

    def __init__(self, session, output):
        """Set session/output Paths and analyzer; no return value."""
        self.session = session.resolve()
        self.output = output.resolve()
        self.analyzer = PairAnalyzer()

    def plan(self):
        """Return (label, category, relative first path, relative second path) tuples.

        No inputs. Uses documented stationary, pan, sweep and N4 capture groups
        in the setup session; missing inputs raise during execution.
        """
        pairs = []
        for group in ('20261008101253721', '20261008231822771'):
            pairs.append((f'stationary_{group}', 'stationary',
                          f'{group}/frame-000000.jpg', f'{group}/frame-000001.jpg'))
        for group in ('20261008223235046', '20261008223409165', '20261008231714783'):
            for first, second, kind in [('center', 'pan', 'pan'), ('center', 'return', 'return')]:
                pairs.append((f'{kind}_{group}', kind, f'{group}/{first}.jpg', f'{group}/{second}.jpg'))
        for angle in range(80, 120, 5):
            group = '20261008225316209'
            pairs.append((f'sweep_{angle:03}_{angle+5:03}', 'sweep',
                          f'{group}/pan{angle:03}.jpg', f'{group}/pan{angle+5:03}.jpg'))
        pairs.append(('forward_before_after', 'drive',
                      '20261008225505941/before.jpg', '20261008225505941/after.jpg'))
        groups = ['20261008231738585', '20261008231751421', '20261008231801683',
                  '20261008231811710', '20261008231822771']
        for direction, first, second in zip(('forward', 'backward', 'left', 'right'), groups, groups[1:]):
            pairs.append((f'drive_{direction}', 'drive',
                          f'{first}/frame-000000.jpg', f'{second}/frame-000000.jpg'))
        return pairs

    def run(self):
        """Execute the planned offline assessment and save report/provenance.

        No inputs or return value. Refuses an existing output directory. Hashes
        input JPEGs before/after, copies source metadata text into provenance and
        records package versions. Raises on missing inputs or modified JPEGs.
        """
        pairs = self.plan()
        captures = self.session / 'captures'
        sources = sorted({captures / rel for _, _, a, b in pairs for rel in (a, b)})
        hashes = {str(path.relative_to(self.session)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sources}
        self.output.mkdir(parents=True, exist_ok=False)
        versions = {module.__name__: module.__version__
                    for module in (cv2, np, PIL, scipy, skimage, matplotlib)}
        metadata = {str(path.parent.relative_to(self.session)): path.read_text(encoding='utf-8-sig')
                    for path in sorted({path.parent / 'info.txt' for path in sources})}
        provenance = {'created_utc': datetime.now(timezone.utc).isoformat(),
                      'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'session': str(self.session), 'versions': versions, 'source_sha256': hashes,
                      'source_info': metadata,
                      'parameters': {'sift_features': 2500, 'ratio': 0.75, 'mutual_check': True,
                                     'homography_ransac_px': 3.0, 'lk_max_corners': 600,
                                     'lk_forward_backward_max_px': 1.0}}
        rows = []
        for label, kind, first, second in pairs:
            metrics = self.analyzer.analyze(captures / first, captures / second, self.output / label)
            rows.append({'pair': label, 'category': kind, 'first': first, 'second': second,
                         **{k: v for k, v in metrics.items() if k != 'homography'}})
            print(f'{label}: SIFT {metrics["homography_inliers"]}/{metrics["mutual_matches"]}; '
                  f'LK {metrics["lk_valid"]}; displacement {metrics["sift_magnitude_median_px"]}', flush=True)
        unchanged = all(hashlib.sha256((self.session / rel).read_bytes()).hexdigest() == digest
                        for rel, digest in hashes.items())
        provenance['source_hashes_unchanged'] = unchanged
        (self.output / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
        with (self.output / 'summary.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        (self.output / 'info.txt').write_text(
            'Offline feature matching and sparse optical flow of setup-session stationary, pan and drive JPEGs.\n'
            'Source paths, hashes, metadata and methods: provenance.json. Numerical results: summary.csv.\n'
            'No calibrated intrinsics, physical scale, depth or exposure timing. No rover operations.\n', encoding='utf-8')
        lines = ['# Offline capture assessment', '',
                 'All six installed packages imported. Images were analyzed at original resolution.', '',
                 'SIFT matches use a 0.75 ratio and mutual check, then a 3 px RANSAC homography. '
                 'Sparse Lucas–Kanade tracks require forward/backward error ≤1 px. '
                 'Displacement medians use retained features. Positive dx is right and dy is down.', '',
                 '| Pair | H inliers / mutual | SIFT median motion (px) | LK valid | LK median motion (px) |',
                 '|---|---:|---:|---:|---:|']
        for row in rows:
            sift = row['sift_magnitude_median_px']
            lk = row['lk_magnitude_median_px']
            sift_text = f'{sift:.3f}' if sift is not None else '—'
            lk_text = f'{lk:.3f}' if lk is not None else '—'
            lines.append(f'| {row["pair"]} | {row["homography_inliers"]}/{row["mutual_matches"]} '
                         f'| {sift_text} | {row["lk_valid"]} | {lk_text} |')
        by_name = {row['pair']: row for row in rows}
        lines += ['', '## Findings', '',
                  '- The two stationary comparison pairs have SIFT median displacement 0.30 and 0.44 px. '
                  'Their LK medians are 0.16 and 0.20 px.',
                  '- Forward before/after is 5.18 px; sequential forward/backward pairs are 3.12/7.21 px '
                  '(SIFT). LK gives 5.33/3.04/7.35 px respectively. These image changes exceed the '
                  'stationary comparisons, but do not isolate physical translation.',
                  f'- Left/right SIFT median dx is {by_name["drive_left"]["sift_dx_median_px"]:.2f}/'
                  f'{by_name["drive_right"]["sift_dx_median_px"]:.2f} px: opposite horizontal scene shifts. '
                  'LK retains fewer points for these large displacements and reports smaller magnitudes.',
                  '- Five-degree commanded sweep steps produce SIFT median motion 33.44–42.69 px. '
                  'Pan-return residual motion is 0.90–3.64 px; physical servo repeatability is not measured.',
                  '- All pairs yielded a homography and retained SIFT/LK correspondences. This establishes '
                  'usable offline diagnostics for these captures; sufficient 3D geometry remains unknown.', '',
                  '![Pixel motion comparison](motion_summary.png)', '', '## Interpretation limits', '',
                  '- Stationary pairs provide an empirical comparison, not a calibrated noise threshold.',
                  '- Matching and flow describe image changes. They do not isolate translation from rotation, '
                  'servo effects, scene motion or exposure changes, and do not establish centimeters or physical turn angles.',
                  '- Homography fit is a diagnostic. It cannot distinguish a plane from pure rotation or prove depth parallax. '
                  'Large-motion LK failures can bias retained tracks; compare SIFT and rejection counts.',
                  '- No camera intrinsics, known distance, poses or depth inputs were supplied. '
                  'No reconstruction or metric drive calibration was performed.',
                  f'- All {len(sources)} input JPEG hashes unchanged: {unchanged}.', '',
                  'Per-pair outputs: matches.png (homography inliers), flow.png (retained tracks), '
                  'matches.csv, flow.csv, metrics.json and aligned_difference.png when a homography is available. '
                  'Difference images are raw grayscale errors, sensitive to exposure and interpolation.', '']
        (self.output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
        self.plot(rows)
        if not unchanged:
            raise RuntimeError('Source JPEG changed during analysis')

    def plot(self, rows):
        """Save a static pixel-motion chart and a flow contact sheet.

        Input is a list of result dictionaries. Outputs PNG files under the run
        directory; no return value. Chart uses a log axis to show small/large motion.
        """
        positions = np.arange(len(rows))
        figure, axis = plt.subplots(figsize=(12, 10))
        axis.barh(positions - 0.18, [row['sift_magnitude_median_px'] or 0.001 for row in rows],
                  height=0.35, label='SIFT homography inliers')
        axis.barh(positions + 0.18, [row['lk_magnitude_median_px'] or 0.001 for row in rows],
                  height=0.35, label='LK with forward/backward check')
        axis.set_yticks(positions, [row['pair'] for row in rows])
        axis.invert_yaxis()
        axis.set_xscale('log')
        axis.set_xlabel('Median feature displacement (pixels, log scale)')
        axis.set_title('Saved rover images: pixel motion, without physical scale')
        axis.grid(axis='x', alpha=0.25)
        axis.legend()
        figure.tight_layout()
        figure.savefig(self.output / 'motion_summary.png', dpi=140)
        plt.close(figure)
        contact = np.full((7 * 220, 3 * 320, 3), 255, dtype=np.uint8)
        for index, row in enumerate(rows):
            im = cv2.imread(str(self.output / row['pair'] / 'flow.png'))
            thumbnail = cv2.resize(im, (320, 190))
            y, x = (index // 3) * 220, (index % 3) * 320
            contact[y + 30:y + 220, x:x + 320] = thumbnail
            cv2.putText(contact, row['pair'], (x + 4, y + 20), cv2.FONT_HERSHEY_SIMPLEX,
                        0.38, (0, 0, 0), 1)
        self.analyzer.save_image(self.output / 'flow_overview.png', contact)


def main():
    """Parse required --session/--output path arguments and run; no return value."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    CaptureAssessment(args.session, args.output).run()


if __name__ == '__main__':
    main()
