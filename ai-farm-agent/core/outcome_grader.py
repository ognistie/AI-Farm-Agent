"""Offline acceptance grader: independently reads fixture artifacts, never executes traces.

Selection, process status and artifact outcome are separate. Trace text is not evidence.
This grader covers files/refusals, not the state of a live GUI or audio quality.
"""
import hashlib
from pathlib import Path

VERSION = '1.0'


def grade(case, trace, fixture_root):
    root = Path(fixture_root).resolve()
    expected = case.get('expected_agents')
    selection = None if expected is None else sorted(expected) == sorted(trace.get('agents', []))
    process = trace.get('status') in case.get('accepted_statuses', ['succeeded'])
    checks = case.get('artifacts', [])
    outcomes = []
    for check in checks:
        relative = Path(check['path'])
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root):
            outcomes.append(False)
            continue
        if check.get('absent'):
            outcomes.append(not path.exists())
            continue
        if not path.is_file() or path.stat().st_size > 1024 * 1024:
            outcomes.append(False)
            continue
        data = path.read_bytes()
        if 'sha256' in check:
            outcomes.append(hashlib.sha256(data).hexdigest() == check['sha256'])
        elif 'contains' in check:
            outcomes.append(check['contains'] in data.decode('utf-8', 'replace'))
        else:
            outcomes.append(False)  # existence alone cannot stand in for file correctness
    return {'grader_version': VERSION, 'selection': selection, 'process': process,
            'outcome': bool(checks) and all(outcomes), 'checks': outcomes}
