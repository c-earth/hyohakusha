"""Measure target/background differential motion in two saved full images.

Inputs specify a session, first/second JPEGs, separate endpoint target ROIs in
pixels and a new output directory. Outputs retain unique SIFT matches, LK tracks,
static-subset H/F diagnostics and source hashes. No metric camera model is used.
"""

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from src.agent.analysis.capture_readiness import ReadinessAssessment


class TargetBaselineAssessment:
    """Own endpoint masks and saved correspondence assessment without hardware.

    Attributes hold paths and separate target bounding boxes (x0,y0,x1,y1).
    Background excludes each target x-band below its top and rightmost 20%.
    Masks are scene-specific and cannot assert object identity or rigidity.
    """

    def __init__(self, session, first, second, first_roi, second_roi, output):
        """Set source paths, endpoint pixel ROIs and new output path."""
        self.session = session.resolve()
        self.first, self.second = first.resolve(), second.resolve()
        self.first_roi, self.second_roi = first_roi, second_roi
        self.output = output.resolve()
        self.readiness = ReadinessAssessment(session, output, last_run=self.second.parent.name)

    @staticmethod
    def load_points(path):
        """Return CSV records and paired full-image pixel arrays."""
        with path.open(encoding='utf-8') as handle:
            rows = list(csv.DictReader(handle))
        a = np.array([[float(r['x1_px']), float(r['y1_px'])] for r in rows]).reshape(-1, 2)
        b = np.array([[float(r['x2_px']), float(r['y2_px'])] for r in rows]).reshape(-1, 2)
        return rows, a, b

    @staticmethod
    def inside(points, roi):
        """Return point-membership mask for the half-open endpoint ROI."""
        x0, y0, x1, y1 = roi
        return ((points[:, 0] >= x0) & (points[:, 0] < x1)
                & (points[:, 1] >= y0) & (points[:, 1] < y1))

    @staticmethod
    def background(points, roi, width):
        """Exclude endpoint target/support x-band and rightmost clothing region."""
        x0, y0, x1, _ = roi
        return (((points[:, 0] < x0) | (points[:, 0] >= x1) | (points[:, 1] < y0))
                & (points[:, 0] < 0.8 * width))

    def run(self):
        """Save correspondence diagnostics and evaluate target against background.

        Hashes input JPEGs before/after. Target points are held out from background
        H fitting; F assessment uses combined static candidate points. Held-out
        F splits remain within-pair checks, not independent reconstruction proof.
        """
        sources = (self.first, self.second)
        hashes = {str(p.relative_to(self.session)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        self.output.mkdir(parents=True, exist_ok=False)
        full = self.readiness.analyzer.analyze(*sources, self.output / 'full')
        records, a, b = self.load_points(self.output / 'full' / 'matches.csv')
        width = full['width_px']
        target = self.inside(a, self.first_roi) & self.inside(b, self.second_roi)
        background = self.background(a, self.first_roi, width) & self.background(b, self.second_roi, width)
        static = target | background
        static_h_mask = np.zeros(int(static.sum()), dtype=bool)
        static_h_residual = np.full(int(static.sum()), np.nan)
        if static.sum() >= 4:
            cv2.setRNGSeed(0)
            static_h, fitted_mask = cv2.findHomography(a[static], b[static], cv2.RANSAC, 3.0)
            if static_h is not None and fitted_mask is not None:
                static_h_mask = fitted_mask.ravel().astype(bool)
                static_h_residual = np.linalg.norm(cv2.perspectiveTransform(a[static,None],static_h)[:,0]-b[static],axis=1)
        static_csv = self.output / 'static_matches.csv'
        with static_csv.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]) + ['region'] if records else ['x1_px','y1_px','x2_px','y2_px','homography_inlier','residual_px','region'])
            writer.writeheader()
            selected_index = 0
            for record, keep, object_point in zip(records, static, target):
                if keep:
                    writer.writerow({**record, 'homography_inlier': int(static_h_mask[selected_index]),
                                     'residual_px': float(static_h_residual[selected_index]),
                                     'region': 'target' if object_point else 'background'})
                    selected_index += 1
        metrics = {'full_mutual_matches': len(a), 'static_unique_matches': int(static.sum()),
                   'static_h_inliers': int(static_h_mask.sum()),
                   'target_unique_sift_matches': int(target.sum()), 'background_unique_sift_matches': int(background.sum()),
                   **self.readiness.projective_check(static_csv),
                   **{'static_' + k: v for k,v in self.readiness.distribution(static_csv,width,full['height_px']).items()}}
        h = None
        if background.sum() >= 4:
            cv2.setRNGSeed(0)
            h, mask = cv2.findHomography(a[background], b[background], cv2.RANSAC, 3.0)
            if h is not None:
                error = cv2.perspectiveTransform(a[background,None],h)[:,0] - b[background]
                metrics['background_h_inliers'] = int(mask.sum())
                metrics['background_h_fit_median_px'] = float(np.median(np.linalg.norm(error[mask.ravel().astype(bool)],axis=1)))
                metrics['background_h'] = h.tolist()
        target_rows = []
        for kind, points_first, points_second in [('sift',a[target],b[target]),('lk',None,None)]:
            if kind == 'lk':
                _, p, q = self.load_points(self.output / 'full' / 'flow.csv')
                keep = self.inside(p,self.first_roi) & self.inside(q,self.second_roi)
                points_first,points_second = p[keep],q[keep]
            metrics[f'target_{kind}_n'] = len(points_first)
            if h is not None and len(points_first):
                predicted = cv2.perspectiveTransform(points_first[:,None],h)[:,0]
                residual = points_second - predicted
                metrics[f'target_{kind}_background_h_residual_median_px'] = float(np.median(np.linalg.norm(residual,axis=1)))
                metrics[f'target_{kind}_residual_dx_median_px'] = float(np.median(residual[:,0]))
                metrics[f'target_{kind}_residual_dy_median_px'] = float(np.median(residual[:,1]))
                target_rows += [[kind,*p,*q,*r,float(np.linalg.norm(r))] for p,q,r in zip(points_first,points_second,residual)]
        with (self.output/'target_residuals.csv').open('w',newline='',encoding='utf-8') as handle:
            writer=csv.writer(handle)
            writer.writerow(['method','x1_px','y1_px','x2_px','y2_px','residual_dx_px','residual_dy_px','residual_norm_px'])
            writer.writerows(target_rows)
        unchanged = all(hashlib.sha256((self.session/p).read_bytes()).hexdigest()==digest for p,digest in hashes.items())
        inventory = self.readiness.inventory()
        relevant = [row for row in inventory if self.first.parent.name <= row['run'] <= self.second.parent.name]
        (self.output/'inventory.json').write_text(json.dumps(relevant,indent=2),encoding='utf-8')
        (self.output/'metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
        provenance = {'created_utc':datetime.now(timezone.utc).isoformat(), 'source_sha256':hashes,
                      'source_hashes_unchanged':unchanged, 'first_roi_xyxy':self.first_roi,'second_roi_xyxy':self.second_roi,
                      'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'readiness_script_sha256':hashlib.sha256(Path(__file__).with_name('capture_readiness.py').read_bytes()).hexdigest(),
                      'parameters':'SIFT deduplicated by rounded pixel location; mutual ratio0.75; H RANSAC3px; F RANSAC1px; LK FB<=1px'}
        (self.output/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
        report=['# Endpoint target baseline assessment','',f'First: {self.first.relative_to(self.session)}',f'Second: {self.second.relative_to(self.session)}','',
                'Endpoint-specific target masks retain full-image coordinates. Background excludes the target/support band and rightmost20% in both images. See inventory.json for recorded motion directions and validator eligibility.','',
                '```json',json.dumps({k:v for k,v in metrics.items() if k not in ('background_h','fundamental_matrix')},indent=2),'```','',
                'Target/background differential residual is a parallax candidate, not physical depth. Background H can be poorly conditioned; combined F can also be degenerate. SIFT and LK agreement adds corroboration but shares the same images. Alternating held-out points are not an independent third view.','',
                'A projective point cloud has arbitrary gauge and scale; no metric interpretation is justified without calibration/scale. Raw two-view fitting must be assessed against an additional view and rigid target correspondence. Source JPEG hashes unchanged: '+str(unchanged)]
        (self.output/'report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
        if not unchanged:
            raise RuntimeError('Source JPEG changed')
        print(json.dumps({k:v for k,v in metrics.items() if k not in ('background_h','fundamental_matrix')},indent=2))


def main():
    """Parse saved-image paths and pixel masks, then perform the offline analysis."""
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('session','first','second','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--first-roi',nargs=4,type=int,required=True)
    parser.add_argument('--second-roi',nargs=4,type=int,required=True)
    args=parser.parse_args()
    TargetBaselineAssessment(args.session,args.first,args.second,args.first_roi,args.second_roi,args.output).run()


if __name__=='__main__':
    main()
