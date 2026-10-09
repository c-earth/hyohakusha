"""Create an offline evidence card for one saved segment, never movement permission.

Inputs are session directory, numeric run stamp and a new output directory.
Retains MotionValidation diagnostics and inventory. False/unknown support does
not become a pass merely because this reporting process exits successfully.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from src.agent.analysis.session_brief import SessionBrief
from src.agent.analysis.validate_motion import MotionValidation


class SegmentReview:
    """Combine explicit completion, stopped rest, cleanup and battery evidence.

    session/run locate immutable saved inputs; output must be newly created and
    outside the raw logs/captures trees. support is an evidence predicate only:
    no metric pose, clearance, route selection or runtime authorization follows.
    """

    def __init__(self, session, run, output):
        """Resolve saved inputs and refuse output nested inside raw data trees."""
        self.session, self.output = Path(session).resolve(), Path(output).resolve()
        self.run = run
        if not str(run).isdigit():
            raise ValueError('Run must be a numeric acquisition stamp')
        if any(self.output.is_relative_to(self.session / kind) for kind in ('logs', 'captures')):
            raise ValueError('Output must be outside raw logs/captures')

    @staticmethod
    def evidence_card(validation, inventory, error=None):
        """Compute strict saved-evidence support from validator/inventory dicts.

        Require nonempty explicit complete trials, pre/post accepted rest,
        matching trial counts, clean event records and finite battery >=7.0 V.
        Missing values fail support and are retained as unknown where applicable.
        """
        trials = validation.get('trials', [])
        complete = bool(trials) and all(item.get('status') == 'complete' for item in trials)
        rest = bool(trials) and all(item.get('pre_rest', {}).get('accepted') is True
                                   and item.get('post_rest', {}).get('accepted') is True for item in trials)
        battery = inventory.get('minimum_battery_v')
        battery_supported = (isinstance(battery, (int, float)) and not isinstance(battery, bool)
                             and math.isfinite(battery) and battery >= 7.0)
        gates = dict(explicit_complete_trials=complete, pre_post_rest_supported=rest,
                     validator_acquisition_complete=validation.get('acquisition_complete') is True,
                     inventory_acquisition_complete=inventory.get('acquisition_complete') is True,
                     positive_cleanup=inventory.get('positive_cleanup') is True
                                      and validation.get('cleanup_recorded') is True,
                     no_event_errors=validation.get('event_errors') == [] and inventory.get('read_errors') == [],
                     no_acquisition_failures=validation.get('acquisition_failures') == [] and inventory.get('failures') == [],
                     matching_trial_count=bool(trials) and len(trials) == inventory.get('trials'),
                     battery_supported=battery_supported, validation_succeeded=error is None)
        return dict(schema_version=1, saved_evidence_supported=all(gates.values()), gates=gates,
                    minimum_battery_v=battery, latest_battery_v=inventory.get('latest_battery_v'),
                    observations=inventory.get('observations', []), latest_capture=inventory.get('latest_capture'),
                    validation_error=error, clearance_verified=False, movement_authorized=False,
                    limitations=['Offline evidence card; reporting success is not evidence support.',
                                 'Rest thresholds are provisional; command cleanup does not establish physical stop latency.',
                                 'Battery accuracy, metric pose, full-body clearance and routes remain unverified.'])

    def assess(self):
        """Retain unsupported/error cards alongside any partial validation files."""
        self.output.mkdir(parents=True, exist_ok=False)
        inventory_reader = SessionBrief(self.session, self.run)
        inventory = inventory_reader.run_summary(self.session / 'logs' / self.run)
        validation, error = {}, None
        try:
            MotionValidation(self.session / 'logs' / self.run, self.output / 'validation').run()
            validation = json.loads((self.output / 'validation' / 'validation.json').read_text(encoding='utf-8'))
        except Exception as failure:
            error = f'{type(failure).__name__}: {failure}'
        card = self.evidence_card(validation, inventory, error)
        card.update(session=str(self.session), run=self.run, sources_sha256=inventory_reader.sources,
                    review_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        (self.output / 'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
        (self.output / 'decision.json').write_text(json.dumps(card, indent=2), encoding='utf-8')
        lines = ['# Saved segment evidence card', '', f"Saved evidence supported: {card['saved_evidence_supported']}",
                 '', '| Evidence predicate | Supported |', '|---|---|']
        lines += [f'| {key} | {value} |' for key, value in card['gates'].items()]
        lines += ['', f'Validation error: {error}', '', *card['limitations'], '',
                  'Clearance verified: false. Movement authorized: false.']
        (self.output / 'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        return card


def main():
    """Write the evidence card and print its support value and absolute path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', type=Path)
    parser.add_argument('--run', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    card = SegmentReview(args.session, args.run, args.output).assess()
    print(f"Saved evidence supported: {card['saved_evidence_supported']}")
    print(str((args.output / 'decision.json').resolve()))
    print(str((args.output / 'report.md').resolve()))


if __name__ == '__main__':
    main()
