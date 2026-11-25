"""Freeze the paired pilot for the 19-block hybrid and score generated answers."""
import argparse
import json
from pathlib import Path

from evaluate import prepare, score, summarize, write

IDS = {'N029V/chunks', 'G043/edges', 'N028VG/3', 'N028VG/6',
       'G043/pt-math', 'G043/en-order', 'G043/echo-code', 'G043/echo-pt'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--score', action='store_true')
    args = parser.parse_args()
    folder = args.folder
    if not args.score:
        prepare(folder)
        prompts = json.loads((folder / 'prompts.json').read_text())
        keys = json.loads((folder / 'grading.json').read_text())
        chosen = [row for row in prompts if row['id'] in IDS]
        assert len(chosen) == len(IDS)
        write(folder / 'prompts.json', chosen)
        write(folder / 'grading.json', {key: keys[key] for key in sorted(IDS)})
    else:
        prompts = json.loads((folder / 'prompts.json').read_text())
        keys = json.loads((folder / 'grading.json').read_text())
        variants = {name: score(folder / f'{name}.jsonl', prompts, keys)
                    for name in ('base', 'lexicon', 'hybrid')}
        report = {}
        for name, rows in variants.items():
            groups = summarize(rows, variants['base'])
            assert all(not group['errors'] for group in groups.values()), groups
            report[name] = {'correct': sum(row['correct'] for row in rows), 'count': len(rows),
                            'wall_seconds': sum(row['seconds'] for row in rows), 'groups': groups,
                            'answers': [{k: row.get(k) for k in ('id', 'correct', 'passed_cases',
                                          'total_cases', 'finish_reason', 'final')} for row in rows]}
        write(folder / 'resultado.json', report)
