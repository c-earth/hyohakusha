"""Summarize saved session evidence without importing a controller or contacting hardware.

The CLI accepts a session directory and optional last-run cutoff. JSON goes to
stdout unless a new output directory is requested. Echo distance assumes 343 m/s
and a round trip; it is neither verified clearance nor a route recommendation.
"""

import argparse
from collections import Counter
import hashlib
import html
import json
import math
from pathlib import Path


class SessionBrief:
    """Inventory saved runs, retaining parse failures and unknown cleanup.

    session is the data directory containing logs/captures. last_run freezes the
    lexicographic timestamp cutoff. Sources are hashed; acquisition data is read
    only. Missing status is unknown rather than silently counted as complete.
    """

    def __init__(self, session, last_run=None):
        """Resolve the saved session path and freeze an optional run-stamp cutoff."""
        self.session = Path(session).resolve()
        self.last_run = last_run
        self.sources = {}

    def read(self, path):
        """Read a UTF-8 source and retain its SHA256 for report provenance."""
        data = path.read_bytes()
        self.sources[str(path)] = hashlib.sha256(data).hexdigest()
        return data.decode('utf-8-sig')

    @staticmethod
    def distance(echo):
        """Convert finite positive round-trip microseconds to approximate meters."""
        if isinstance(echo, (int, float)) and not isinstance(echo, bool) and math.isfinite(echo) and echo > 0:
            return echo * 343 / 2000000
        return None

    def run_summary(self, folder):
        """Read one run, retaining malformed records instead of inventing success."""
        errors, trials, events = [], [], []
        manifest = folder / 'trials.json'
        if manifest.exists():
            try:
                trials = json.loads(self.read(manifest))
                if not isinstance(trials, list) or any(not isinstance(item, dict) for item in trials):
                    raise ValueError('trials.json must contain a list of objects')
            except (ValueError, OSError, UnicodeError) as error:
                trials = []
                errors.append(str(error))
        else:
            errors.append('Missing trials.json; movement count unknown')
        event_path = folder / 'events.jsonl'
        if event_path.exists():
            try:
                for number, line in enumerate(self.read(event_path).splitlines(), 1):
                    try:
                        event = json.loads(line)
                        if not isinstance(event, dict) or not isinstance(event.get('payload', {}), dict):
                            raise ValueError('event/payload must be objects')
                        events.append(event)
                    except ValueError:
                        errors.append(f'Invalid events.jsonl line {number}')
            except (OSError, UnicodeError) as error:
                errors.append(str(error))
        else:
            errors.append('Missing events.jsonl')
        failures = [event for event in events if event.get('kind') in ('failure', 'cleanup_failure')]
        cleanup = next((event.get('payload', {}) for event in reversed(events) if event.get('kind') == 'cleanup'), None)
        positive_cleanup = bool(cleanup and cleanup.get('stop_attempted') is True and cleanup.get('socket_closed') is True
                                and not cleanup.get('stop_error') and not any(event.get('kind') == 'cleanup_failure' for event in events))
        battery = [event['payload'].get('voltage_v') for event in events if event.get('kind') == 'battery']
        battery = [value for value in battery if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)]
        captures = self.session / 'captures' / folder.name
        views = []
        for trial in trials:
            for field in ('first', 'second', 'later'):
                if isinstance(trial.get(field), str):
                    candidate = (captures / trial[field]).resolve()
                    if candidate.is_relative_to(captures.resolve()):
                        views.append(dict(kind=field, path=str(candidate), exists=candidate.is_file()))
        echo = next((trial.get('after', {}).get('echo_us') for trial in reversed(trials)
                     if isinstance(trial.get('after'), dict) and 'echo_us' in trial['after']), None)
        counts = Counter(str(trial.get('status', 'unknown')) for trial in trials)
        observations = []
        for index, trial in enumerate(trials):
            before = trial.get('before') if isinstance(trial.get('before'), dict) else {}
            after = trial.get('after') if isinstance(trial.get('after'), dict) else {}
            first_echo, last_echo = before.get('echo_us'), after.get('echo_us')
            change = ((last_echo - first_echo) / first_echo * 100
                      if self.distance(first_echo) is not None and self.distance(last_echo) is not None else None)
            observations.append(dict(index=index, status=trial.get('status', 'unknown'),
                                     direction=trial.get('direction'), echo_before_us=first_echo,
                                     echo_after_us=last_echo, echo_change_percent=change,
                                     host_stop_elapsed_ms=trial.get('host_stop_elapsed_ms')))
        return dict(run=folder.name, counts=dict(counts), trials=len(trials),
                    observations=observations,
                    directions=dict(Counter(str(trial.get('direction', 'unknown')) for trial in trials)),
                    trial_errors=[dict(index=index, status=trial.get('status', 'unknown'), error=trial.get('error'))
                                  for index, trial in enumerate(trials) if trial.get('status') != 'complete'],
                    acquisition_complete=bool(any(event.get('kind') == 'complete' for event in events)
                                              and all(trial.get('status') == 'complete' for trial in trials)
                                              and positive_cleanup and not failures and not errors),
                    positive_cleanup=positive_cleanup, cleanup=cleanup,
                    failures=failures, read_errors=errors,
                    latest_battery_v=battery[-1] if battery else None,
                    minimum_battery_v=min(battery) if battery else None,
                    latest_echo_us=echo, approximate_echo_distance_m=self.distance(echo),
                    latest_capture=views[-1] if views else None)

    def assess(self):
        """Return a timestamp-ordered inventory and aggregate observed counts."""
        logs = self.session / 'logs'
        if not logs.is_dir():
            raise ValueError('Session must contain a logs directory')
        folders = sorted(path for path in logs.iterdir() if path.is_dir() and path.name.isdigit()
                         and (self.last_run is None or path.name <= self.last_run))
        runs = [self.run_summary(folder) for folder in folders]
        self.sources[str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        counts = Counter()
        for run in runs:
            counts.update(run['counts'])
        return dict(schema_version=1, session=str(self.session), last_run=self.last_run,
                    counts=dict(counts), runs=runs, sources_sha256=self.sources,
                    limitations=['Saved evidence only; no hardware contact.',
                                 'Positive cleanup records a stop attempt and socket close, not physical rest.',
                                 'Echo conversion assumes sound speed 343 m/s; reflecting target and path clearance are unknown.',
                                 'Missing manifests/status/events remain unknown; counts do not infer unsaved motion.'])


def main():
    """Print JSON or save JSON/Markdown in a newly created output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('session', type=Path)
    parser.add_argument('--last-run')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = SessionBrief(args.session, args.last_run).assess()
    encoded = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        destination = args.output.resolve()
        session = args.session.resolve()
        if any(destination.is_relative_to(session / category) for category in ('logs', 'captures')):
            parser.error('Output must be outside raw logs/captures')
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / 'summary.json').write_text(encoded, encoding='utf-8')
        lines = ['# Saved session brief', '', f"Trial status counts: {report['counts']}", '',
                 '| Run | Trial statuses | Cleanup record | Latest battery V | Echo us / approximate m | Latest capture |',
                 '|---|---|---|---|---|---|']
        for run in report['runs']:
            view = run['latest_capture']
            link = f"[capture](<{view['path']}>)" if view else 'unknown'
            lines.append(f"| {run['run']} | {run['counts']} | {run['positive_cleanup']} | {run['latest_battery_v']} | {run['latest_echo_us']} / {run['approximate_echo_distance_m']} | {link} |")
        lines += ['', *report['limitations']]
        (args.output / 'report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
        rows = []
        for run in report['runs']:
            view = run['latest_capture']
            capture = (f'<a href="{html.escape(Path(view["path"]).as_uri())}">Latest capture</a>'
                       if view and view['exists'] else 'unknown / unavailable')
            values = [run['run'], run['counts'], run['positive_cleanup'], run['latest_battery_v'],
                      f"{run['latest_echo_us']} / {run['approximate_echo_distance_m']}",
                      run['read_errors'], [event['payload'] for event in run['failures']]]
            rows.append('<tr>'+''.join(f'<td>{html.escape(str(value))}</td>' for value in values)+f'<td>{capture}</td></tr>')
        cards = []
        for run in report['runs']:
            for observation in run['observations']:
                change = observation['echo_change_percent']
                formatted = f'{change:+.2f}%' if change is not None else 'unknown'
                cards.append(f'<li>{html.escape(run["run"])} / trial {observation["index"]}: '
                             f'{html.escape(str(observation["direction"]))}, {html.escape(str(observation["status"]))}; '
                             f'echo {html.escape(str(observation["echo_before_us"]))} → '
                             f'{html.escape(str(observation["echo_after_us"]))} µs ({formatted}); '
                             f'host stop elapsed {html.escape(str(observation["host_stop_elapsed_ms"]))} ms.</li>')
        document = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Saved rover session</title>'
                    '<style>body{font:16px system-ui;margin:2rem;background:#f5f7fa;color:#152334}'
                    'table{border-collapse:collapse;background:white;width:100%}td,th{padding:.7rem;border:1px solid #ccd4de;text-align:left}'
                    'li{margin:.6rem 0}h1{margin-bottom:.5rem}</style><h1>Saved rover session</h1>'
                    f'<p>Observed trial statuses: {html.escape(str(report["counts"]))}</p><ul>'
                    + ''.join(f'<li>{html.escape(item)}</li>' for item in report['limitations'])
                    + '</ul><table><thead><tr><th>Run</th><th>Statuses</th><th>Stop attempt / socket closed</th>'
                    '<th>Latest battery V</th><th>Echo us / approximate m</th><th>Read errors</th><th>Failures</th><th>Capture</th>'
                    '</tr></thead><tbody>'+''.join(rows)+'</tbody></table><h2>Per-trial observations</h2>'
                    '<p>Signed echo change compares before/after values. Turns change beam direction; '
                    'host stop elapsed measures command timing, not physical stopping latency.</p><ul>'
                    + ''.join(cards) + '</ul></html>')
        (args.output / 'report.html').write_text(document, encoding='utf-8')
        for filename in ('summary.json', 'report.md', 'report.html'):
            print(str((args.output / filename).resolve()))
    else:
        print(encoded)


if __name__ == '__main__':
    main()
