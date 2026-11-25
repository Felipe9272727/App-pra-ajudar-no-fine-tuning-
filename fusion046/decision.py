"""Select the candidate on development data and decide promotion after held-out scoring."""
import argparse
import hashlib
import json
from pathlib import Path


def metrics(row):
    group = row['groups']
    return (row['passed'], group['Código']['code_cases'], group['Controles']['passed'])


def eligible(candidate, baseline):
    return all(a >= b for a, b in zip(metrics(candidate), metrics(baseline)))


def select(screen, fit, frozen):
    rows = json.loads(screen.read_text())
    report = json.loads(fit.read_text())
    flags = {name: eligible(rows[name], rows['parent']) for name in ('readout', 'balanced')}
    variant = max(flags, key=lambda name: (flags[name], *metrics(rows[name]), name == 'readout'))
    return {'variant': variant, 'eligible_screen': flags[variant], 'eligible_candidates': flags,
            'candidates': report['candidates'], 'parent': report['parent'],
            'frozen_suite_sha256': hashlib.sha256(frozen.read_bytes()).hexdigest(),
            'screen_metrics': {name: metrics(rows[name]) for name in ('parent', 'readout', 'balanced')}}


def finalize(final, selected):
    rows = json.loads(final.read_text())
    freeze = json.loads(selected.read_text())
    name = freeze['variant']
    value, baseline = metrics(rows[name]), metrics(rows['parent'])
    combined = freeze['eligible_screen'] and eligible(rows[name], rows['parent'])
    gains = value[0] > baseline[0] or value[1] > baseline[1]
    return {'variant': name, 'promotion_gate': bool(combined and gains),
            'metrics': {tag: metrics(rows[tag]) for tag in ('base', 'parent', name)},
            'tests': rows[name]['count'], 'candidate_sha256': freeze['candidates'][name]['sha256']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=('screen', 'final'))
    p.add_argument('report', type=Path)
    p.add_argument('evidence', type=Path)
    p.add_argument('--frozen', type=Path)
    a = p.parse_args()
    result = select(a.report, a.evidence, a.frozen) if a.phase == 'screen' else finalize(a.report, a.evidence)
    print(json.dumps(result, ensure_ascii=False, indent=2))
