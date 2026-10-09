"""Assess overlap and pixel motion across saved exploration positions offline.

Inputs are session/output paths. Outputs include source hashes, SIFT/LK CSVs,
homography diagnostics and a report. Static-left crops exclude the moving door;
neither homography fit nor image displacement proves depth or metric motion.
"""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from src.agent.analysis.analyze_captures import PairAnalyzer


class UniqueSiftDetector:
    """Retain one SIFT orientation per rounded pixel location, highest response.

    Attribute detector owns SIFT. Removing duplicate orientation keypoints before
    matching prevents nominal point counts and alternating splits from duplicating
    the same image location. This does not guarantee independent spatial samples.
    """

    def __init__(self):
        """Initialize a SIFT detector with the established 2500-feature bound."""
        self.detector = cv2.SIFT_create(nfeatures=2500)

    def detectAndCompute(self, image, mask):
        """Return location-deduplicated keypoints and corresponding descriptors."""
        keypoints, descriptors = self.detector.detectAndCompute(image, mask)
        selected = {}
        for index, point in enumerate(keypoints):
            location = tuple(round(value) for value in point.pt)
            if location not in selected or point.response > keypoints[selected[location]].response:
                selected[location] = index
        indices = sorted(selected.values())
        return [keypoints[index] for index in indices], descriptors[indices] if descriptors is not None else None


class ReadinessAssessment:
    """Own a frozen saved-image inventory and its offline comparison outputs.

    Attributes hold resolved paths, analyzer, run bounds and optional target ROI.
    Crops use original pixels; output coordinates are crop-local. No camera
    model is assumed. Run/focus bounds freeze the saved comparison scope.
    """

    def __init__(self, session, output, last_run=None, focus_run=None, focus_only=False, roi=None, reference_run=None):
        """Set session/output paths and initialize the correspondence analyzer."""
        self.session = session.resolve()
        self.output = output.resolve()
        self.analyzer = PairAnalyzer()
        self.analyzer.detector = UniqueSiftDetector()
        self.last_run = last_run
        self.focus_run = focus_run
        self.focus_only = focus_only
        self.roi = roi
        self.reference_run = reference_run

    def inventory(self):
        """Return manifest trials with explicit completion and optional eligibility.

        All trial metadata are retained; only complete trials whose manifest
        later JPEG exists are selected. Missing status or later fields exclude.
        Validation absence means unknown, not eligible. Paths stay in capture run.
        """
        entries = []
        for manifest in sorted((self.session / 'logs').glob('*/trials.json')):
            run = manifest.parent.name
            if self.last_run is not None and run > self.last_run:
                continue
            validation = self.session / 'analysis' / f'{run}-validation' / 'validation.json'
            validations = json.loads(validation.read_text()).get('trials', []) if validation.exists() else []
            for index, trial in enumerate(json.loads(manifest.read_text())):
                later = trial.get('later')
                path = self.session / 'captures' / run / later if isinstance(later, str) else None
                selected = (trial.get('status') == 'complete' and path is not None
                            and path.parent == self.session / 'captures' / run and path.exists())
                checked = next((row for row in validations if row.get('index') == index), {})
                entries.append({'run': run, 'trial_index': index, 'direction': trial.get('direction'),
                                'early_stop': trial.get('early_stop'), 'pwm': trial.get('pwm'),
                                'duration_ms': trial.get('duration_ms'), 'status': trial.get('status'),
                                'first': trial.get('first'), 'later': later, 'selected': selected,
                                'validation_eligible': checked.get('eligible'),
                                'pre_rest_accepted': checked.get('pre_rest', {}).get('accepted'),
                                'post_rest_accepted': checked.get('post_rest', {}).get('accepted'),
                                'manifest': str(manifest.relative_to(self.session)),
                                'validation': str(validation.relative_to(self.session)) if validation.exists() else None})
        return entries

    @staticmethod
    def distribution(path, width, height, inliers=False):
        """Measure occupied 4x3 cells and bounding-box area for retained points.

        CSV input coordinates are pixels; outputs are cell count and image-area
        fraction. Bounding boxes measure distribution, not valid scene coverage.
        """
        with path.open(encoding='utf-8') as handle:
            rows = [r for r in csv.DictReader(handle)
                    if not inliers or r['homography_inlier'] == '1']
        points = np.array([[float(r['x1_px']), float(r['y1_px'])] for r in rows])
        if not len(points):
            return {'occupied_cells_of_12': 0, 'bbox_area_fraction': 0.0}
        cells = {(min(3, int(x * 4 / width)), min(2, int(y * 3 / height)))
                 for x, y in points}
        span = np.ptp(points, axis=0)
        return {'occupied_cells_of_12': len(cells),
                'bbox_area_fraction': float(span[0] * span[1] / (width * height))}

    @staticmethod
    def projective_check(path):
        """Fit uncalibrated F on mutual SIFT matches; report Sampson residuals.

        Deterministic alternating matches supply fitting/held-out subsets when
        at least sixteen exist. Residuals are pixel-scaled square-root Sampson
        errors, not depth evidence; planar or rotation degeneracy remains possible.
        """
        with path.open(encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        a = np.array([[float(r['x1_px']), float(r['y1_px'])] for r in rows], dtype=np.float64)
        b = np.array([[float(r['x2_px']), float(r['y2_px'])] for r in rows], dtype=np.float64)
        result = {'fundamental_inliers': None, 'fundamental_sampson_median_px': None,
                  'fundamental_heldout_n': 0, 'fundamental_heldout_median_px': None,
                  'homography_heldout_median_px': None, 'f_inliers_outside_h': None}
        if len(a) < 8:
            return result
        def errors(matrix, p, q):
            ph, qh = np.c_[p, np.ones(len(p))], np.c_[q, np.ones(len(q))]
            fp, ftq = ph @ matrix.T, qh @ matrix
            numerator = np.abs(np.sum(qh * fp, axis=1))
            denominator = np.sqrt(fp[:, 0] ** 2 + fp[:, 1] ** 2 + ftq[:, 0] ** 2 + ftq[:, 1] ** 2)
            return numerator / np.maximum(denominator, 1e-12)
        cv2.setRNGSeed(0)
        matrix, mask = cv2.findFundamentalMat(a, b, cv2.FM_RANSAC, 1.0, 0.99)
        if matrix is not None and matrix.shape == (3, 3) and mask is not None:
            valid = mask.ravel().astype(bool)
            result['fundamental_inliers'] = int(valid.sum())
            result['fundamental_sampson_median_px'] = float(np.median(errors(matrix, a[valid], b[valid]))) if valid.any() else None
            result['fundamental_matrix'] = matrix.tolist()
            h_valid = np.array([r['homography_inlier'] == '1' for r in rows])
            result['f_inliers_outside_h'] = int((valid & ~h_valid).sum())
        if len(a) >= 16:
            cv2.setRNGSeed(0)
            fitted, _ = cv2.findFundamentalMat(a[::2], b[::2], cv2.FM_RANSAC, 1.0, 0.99)
            if fitted is not None and fitted.shape == (3, 3):
                result['fundamental_heldout_n'] = len(a[1::2])
                result['fundamental_heldout_median_px'] = float(np.median(errors(fitted, a[1::2], b[1::2])))
            cv2.setRNGSeed(0)
            fitted_h, _ = cv2.findHomography(a[::2], b[::2], cv2.RANSAC, 3.0)
            if fitted_h is not None:
                projected = cv2.perspectiveTransform(a[1::2, None], fitted_h)[:, 0]
                result['homography_heldout_median_px'] = float(np.median(np.linalg.norm(projected - b[1::2], axis=1)))
        return result

    def foreground_check(self, full_directory, roi_directory):
        """Test target correspondences against a separately fitted background H/F.

        Fixed target ROI coordinates are original pixels. Background excludes
        the target's x band below ROI top and the rightmost 20% (clothes). This
        is scene-specific separation, not semantic detection. SIFT and LK target
        residuals are held out from background fitting, not physical depth units.
        """
        def points(path):
            with path.open(encoding='utf-8') as handle:
                rows = list(csv.DictReader(handle))
            a = np.array([[float(r['x1_px']), float(r['y1_px'])] for r in rows], dtype=np.float64).reshape(-1, 2)
            b = np.array([[float(r['x2_px']), float(r['y2_px'])] for r in rows], dtype=np.float64).reshape(-1, 2)
            return a, b
        a, b = points(full_directory / 'matches.csv')
        x0, y0, x1, y1 = self.roi
        width = json.loads((full_directory / 'metrics.json').read_text())['width_px']
        keep = (((a[:, 0] < x0) | (a[:, 0] >= x1) | (a[:, 1] < y0))
                & ((b[:, 0] < x0) | (b[:, 0] >= x1) | (b[:, 1] < y0))
                & (a[:, 0] < width * 0.8) & (b[:, 0] < width * 0.8))
        result = {'background_matches': int(keep.sum()), 'background_h_inliers': None,
                  'background_exclusion': 'target x-band below ROI top; rightmost 20 percent',
                  'limits': 'Differential residuals can reflect noise; background F can be planar-degenerate.'}
        if keep.sum() < 4:
            return result
        cv2.setRNGSeed(0)
        h, mask = cv2.findHomography(a[keep], b[keep], cv2.RANSAC, 3.0)
        if h is None:
            return result
        result['background_h_inliers'] = int(mask.sum())
        background_errors = np.linalg.norm(cv2.perspectiveTransform(a[keep, None], h)[:, 0] - b[keep], axis=1)
        result['background_h_fit_median_px'] = float(np.median(background_errors[mask.ravel().astype(bool)]))
        fundamental = None
        if keep.sum() >= 8:
            cv2.setRNGSeed(0)
            fundamental, _ = cv2.findFundamentalMat(a[keep], b[keep], cv2.FM_RANSAC, 1.0, 0.99)
        for name, path in [('sift', roi_directory / 'matches.csv'), ('lk', roi_directory / 'flow.csv')]:
            p, q = points(path)
            p, q = p + [x0, y0], q + [x0, y0]
            result[f'target_{name}_n'] = len(p)
            if len(p):
                residual = cv2.perspectiveTransform(p[:, None], h)[:, 0] - q
                result[f'target_{name}_background_h_residual_median_px'] = float(np.median(np.linalg.norm(residual, axis=1)))
                result[f'target_{name}_residual_dx_median_px'] = float(np.median(residual[:, 0]))
                result[f'target_{name}_residual_dy_median_px'] = float(np.median(residual[:, 1]))
                result[f'target_{name}_residual_vectors_px'] = residual.tolist()
                if fundamental is not None and fundamental.shape == (3, 3):
                    ph, qh = np.c_[p, np.ones(len(p))], np.c_[q, np.ones(len(q))]
                    fp, ftq = ph @ fundamental.T, qh @ fundamental
                    sampson = np.abs(np.sum(qh * fp, axis=1)) / np.maximum(np.sqrt(
                        fp[:, 0] ** 2 + fp[:, 1] ** 2 + ftq[:, 0] ** 2 + ftq[:, 1] ** 2), 1e-12)
                    result[f'target_{name}_background_f_sampson_median_px'] = float(np.median(sampson))
        return result

    def run(self):
        """Freeze successful settled views and save comparisons in a new directory.

        First pre-move and complete trial later images come from trials manifests;
        turns and early stops retain their categories. Raises for absent images,
        existing output or changed source bytes. No metric positions are inferred.
        """
        inventory = self.inventory()
        chosen = [entry for entry in inventory if entry['selected']]
        settled = [self.session / 'captures' / entry['run'] / entry['later'] for entry in chosen]
        if len(settled) < 2:
            raise ValueError('Need at least two settled views')
        before = self.session / 'captures' / chosen[0]['run'] / chosen[0]['first'] if chosen[0]['first'] else None
        if before is None or not before.exists():
            raise ValueError('First successful run has no before image')
        pairs = [('first_before_latest', before, settled[-1])]
        pairs += [(f'consecutive_{a.parent.name}_{a.stem}_{b.parent.name}_{b.stem}', a, b)
                  for a, b in zip(settled, settled[1:])]
        if self.focus_run is not None:
            focus = [path for path in settled if path.parent.name == self.focus_run]
            if not focus:
                raise ValueError('Focus run has no settled images')
            reference = self.reference_run or self.focus_run
            reference_trial = next(entry for entry in chosen if entry['run'] == reference)
            focus_before = self.session / 'captures' / reference / reference_trial['first']
            if self.focus_only:
                pairs = []
            pairs += [(f'focus_{self.focus_run}_{path.stem}', focus_before, path) for path in focus]
        sources = sorted({p for _, a, b in pairs for p in (a, b)})
        hashes = {str(p.relative_to(self.session)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sources}
        metadata_paths = sorted({self.session / entry[key] for entry in inventory
                                 for key in ('manifest', 'validation') if entry[key]})
        metadata_hashes = {str(path.relative_to(self.session)): hashlib.sha256(path.read_bytes()).hexdigest()
                           for path in metadata_paths}
        pair_motion = {}
        for label, first, second in pairs:
            start = next((index for index, entry in enumerate(inventory)
                          if entry['run'] == first.parent.name and first.name in (entry['first'], entry['later'])), None)
            end = next((index for index, entry in enumerate(inventory)
                        if entry['run'] == second.parent.name and second.name == entry['later']), None)
            if start is not None and end is not None:
                start += int(first.name == inventory[start]['later'])
                pair_motion[label] = inventory[start:end + 1]
            else:
                pair_motion[label] = None
        self.output.mkdir(parents=True, exist_ok=False)
        (self.output / 'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
        (self.output / 'pair_motion.json').write_text(json.dumps(pair_motion, indent=2), encoding='utf-8')
        rows = []
        for label, first, second in pairs:
            regions = ('full', 'static_left', 'left_column') + (('object_roi',) if self.roi else ())
            for region in regions:
                base = self.output / f'{label}_{region}'
                inputs = (first, second)
                if region != 'full':
                    cropdir = self.output / f'{label}_{region}_crop_inputs'
                    cropdir.mkdir()
                    inputs = tuple(cropdir / f'{i}.png' for i in range(2))
                    for source, target in zip((first, second), inputs):
                        image = cv2.imread(str(source))
                        if image is None:
                            raise ValueError(f'Unreadable {source}')
                        if region == 'object_roi':
                            x0, y0, x1, y1 = self.roi
                            if not (0 <= x0 < x1 <= image.shape[1] and 0 <= y0 < y1 <= image.shape[0]):
                                raise ValueError('ROI outside image bounds')
                            crop = image[y0:y1, x0:x1]
                        else:
                            fraction = 0.5 if region == 'static_left' else 0.55
                            crop = image[:, :int(image.shape[1] * fraction)]
                        self.analyzer.save_image(target, crop)
                metrics = self.analyzer.analyze(*inputs, base)
                metrics.update({f'sift_{k}': v for k, v in self.distribution(
                    base / 'matches.csv', metrics['width_px'], metrics['height_px'], True).items()})
                metrics.update({f'lk_{k}': v for k, v in self.distribution(
                    base / 'flow.csv', metrics['width_px'], metrics['height_px']).items()})
                metrics.update(self.projective_check(base / 'matches.csv'))
                (base / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
                rows.append({'pair': label, 'region': region,
                             'first': str(first.relative_to(self.session)),
                             'second': str(second.relative_to(self.session)),
                             **{k: v for k, v in metrics.items() if k not in ('homography', 'fundamental_matrix')}})
                print(f'{label} {region}: inliers={metrics["homography_inliers"]}, '
                      f'LK={metrics["lk_valid"]}, motion={metrics["sift_magnitude_median_px"]}', flush=True)
            if self.roi:
                diagnostic = self.foreground_check(self.output / f'{label}_full', self.output / f'{label}_object_roi')
                (self.output / f'{label}_foreground.json').write_text(json.dumps(diagnostic, indent=2), encoding='utf-8')
        unchanged = all(hashlib.sha256((self.session / p).read_bytes()).hexdigest() == h
                        for p, h in hashes.items())
        metadata_unchanged = all(hashlib.sha256((self.session / p).read_bytes()).hexdigest() == h
                                 for p, h in metadata_hashes.items())
        provenance = {'created_utc': datetime.now(timezone.utc).isoformat(),
                      'source_sha256': hashes, 'source_hashes_unchanged': unchanged,
                      'metadata_sha256': metadata_hashes, 'metadata_hashes_unchanged': metadata_unchanged,
                      'opencv_version': cv2.__version__, 'numpy_version': np.__version__,
                      'last_run': self.last_run, 'focus_run': self.focus_run,
                      'focus_only': self.focus_only, 'roi_xyxy_original_px': self.roi,
                      'reference_run': self.reference_run,
                      'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'pair_analyzer_sha256': hashlib.sha256(Path(__file__).with_name('analyze_captures.py').read_bytes()).hexdigest(),
                      'static_region': 'left 50 percent, original pixel coordinates',
                      'parameters': {'sift_features': 2500, 'deduplication': 'one keypoint per rounded pixel location', 'mutual_ratio': 0.75,
                                     'ransac_px': 3.0, 'lk_fb_max_px': 1.0}}
        (self.output / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
        with (self.output / 'summary.csv').open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=sorted({k for row in rows for k in row}))
            writer.writeheader()
            writer.writerows(rows)
        report = ['# Saved-view capture readiness', '',
                  'Question: do saved views retain distributed correspondences and measurable image change for further reconstruction assessment?', '',
                  'Inventory selects explicit complete trials from trials.json, including turns and early stops. inventory.json preserves excluded trials and available validator eligibility; pair_motion.json records intervening trial records, including incomplete/refused records. A trial record does not prove command dispatch or physical movement. Missing validation remains unknown. Image displacement is not a metric position.', '',
                  'Frozen settings: SIFT 2500 features, mutual 0.75 ratio, homography RANSAC 3 px; LK forward/backward error <=1 px. Full views and conservative left-half crops are analyzed separately.', '',
                  '| Pair / region | SIFT inliers / mutual | Cells /12 | Median motion px | H residual p90 px | LK valid |',
                  '|---|---:|---:|---:|---:|---:|']
        def fmt(value):
            return 'unknown' if value is None else f'{value:.3f}'
        for row in rows:
            report.append(f'| {row["pair"]} / {row["region"]} | {row["homography_inliers"]}/{row["mutual_matches"]} | {row["sift_occupied_cells_of_12"]} | {fmt(row["sift_magnitude_median_px"])} | {fmt(row["homography_residual_p90_px"])} | {row["lk_valid"]} |')
        minimal = sum(row['homography_inliers'] == 4 for row in rows)
        report += ['', f'{minimal} comparisons have exactly four homography inliers: the minimum fit constraint. Near-zero residuals in these fits are not independent evidence of reliable geometry.']
        report += ['', '## Uncalibrated epipolar diagnostics', '',
                   '| Pair / region | F inliers | F median Sampson px | Held-out count | Held-out median px |',
                   '|---|---:|---:|---:|---:|']
        for row in rows:
            report.append(f'| {row["pair"]} / {row["region"]} | {row["fundamental_inliers"]} | {fmt(row["fundamental_sampson_median_px"])} | {row["fundamental_heldout_n"]} | {fmt(row["fundamental_heldout_median_px"])} |')
        report += ['', '## Interpretation limits', '',
                   'The left-column sensitivity crop extends to 55 percent (440 px at 800 px width); early door edges can intrude into it. Compare with the more conservative 50 percent crop. F fits and alternating held-out Sampson diagnostics are in summary.csv and metrics.json. Insufficient-match cases remain unknown. Epipolar fits can be degenerate in planar scenes or pure rotation, and are not a reconstruction claim.', '',
                   'F RANSAC uses 1 px epipolar distance versus H RANSAC 3 px reprojection distance, so inlier counts are not directly comparable model scores. Held-out errors use alternating descriptor-index order, not independent acquisition. Small fitting samples and nearly planar structure can produce unstable F despite high fitting inlier counts. This assessment does not distinguish a physically valid nonplanar model from a degenerate model.', '',
                   'Correspondences and pixel motion establish overlap/change only. Homography fit can explain rotation, planar scenes or low parallax; residuals can also reflect noise, compression, lighting, or moving objects. They do not independently establish depth, translation, physical stopping distance, or metric scale.', '',
                   'The moving right door/clothes contaminate full-image geometry; left-half cropping is a conservative scene-specific exclusion, not a semantic mask. Floor/path visibility remains limited. Bounding-box fractions and grid occupancy characterize feature distribution, not obstacle clearance.', '',
                   'No intrinsics, guessed focal lengths, triangulation, or pose estimates are used. Reconstruction readiness remains conditional on sufficient static-scene parallax and independently validated geometry.', '',
                   f'Source hashes unchanged: {unchanged}. Detailed coordinates/overlays and per-pair metrics accompany this report.']
        (self.output / 'report.md').write_text('\n'.join(report) + '\n', encoding='utf-8')
        if not unchanged or not metadata_unchanged:
            raise RuntimeError('Source images or metadata changed during analysis')


def main():
    """Parse offline session/output paths and execute the assessment."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--last-run', help='Inclusive capture run ID bound for a frozen block')
    parser.add_argument('--focus-run', help='Also compare first motion-before with each settled image in this run')
    parser.add_argument('--focus-only', action='store_true', help='Restrict comparisons to --focus-run')
    parser.add_argument('--roi', nargs=4, type=int, metavar=('X0', 'Y0', 'X1', 'Y1'), help='Additional fixed ROI in original pixels; saved coordinates are crop-local')
    parser.add_argument('--reference-run', help='First motion-before source run for focused comparisons')
    args = parser.parse_args()
    if args.focus_only and not args.focus_run:
        parser.error('--focus-only requires --focus-run')
    ReadinessAssessment(args.session, args.output, args.last_run, args.focus_run, args.focus_only, args.roi, args.reference_run).run()


if __name__ == '__main__':
    main()
