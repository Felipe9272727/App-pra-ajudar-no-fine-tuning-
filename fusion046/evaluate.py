"""Score deterministic generation. CI receipts omit scratch reasoning and token IDs."""
import argparse
import base64
import json
from pathlib import Path
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from loop042.score import grade


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def receipt(variant, phase, path):
    rows = read(Path(path))
    for row in rows:
        if 'answer' in row:
            row['answer'].pop('raw_text', None)
            row['answer'].pop('generated_ids', None)
    packed = base64.b64encode(zlib.compress(json.dumps(rows, ensure_ascii=False).encode())).decode()
    for index, start in enumerate(range(0, len(packed), 2000)):
        print(f'LS046 {variant} {phase} {index:03d} {packed[start:start+2000]}', flush=True)


def unpack(log, variant, phase, destination):
    prefix = f'LS046 {variant} {phase} '
    parts = {}
    for line in Path(log).read_text(errors='replace').splitlines():
        if prefix in line:
            number, data = line.split(prefix, 1)[-1].strip().split()
            parts[int(number)] = data
    if not parts or sorted(parts) != list(range(len(parts))):
        raise ValueError(f'Incomplete CI receipt for {variant}/{phase}')
    rows = json.loads(zlib.decompress(base64.b64decode(''.join(parts[i] for i in sorted(parts)))))
    Path(destination).write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in rows))


def evaluate(fixtures, phase, results):
    cases = json.loads((fixtures/f'{phase}.prompts.json').read_text())
    keys = json.loads((fixtures/f'{phase}.grading.json').read_text())
    report = {}
    for path in results:
        decoded = read(path)
        assert [row['id'] for row in decoded] == [row['id'] for row in cases], path
        summary, examples = {}, []
        for row in decoded:
            if 'error' in row:
                raise RuntimeError(f'Inference error in {path.name}: {row}')
            answer = row['answer']
            text = answer['text']
            key = keys[row['id']]
            if key['type'] == 'exact':
                passed, details = text.strip() == key['expected'], {}
            else:
                passed, details = grade(text, key)
            group = summary.setdefault(row['group'], {'passed': 0, 'count': 0, 'code_cases': 0, 'total_cases': 0})
            group['passed'] += int(passed)
            group['count'] += 1
            group['code_cases'] += details.get('passed_cases', 0)
            group['total_cases'] += details.get('total_cases', 0)
            examples.append({'id': row['id'], 'passed': bool(passed), 'final': text,
                             'finish': answer['finish_reason'], 'tokens': answer['tokens'], **details})
        report[path.stem] = {'passed': sum(row['passed'] for row in examples), 'count': len(examples),
                             'groups': summary, 'details': examples,
                             'seconds': sum(row['seconds'] for row in decoded),
                             'tokens': sum(row['tokens'] for row in examples)}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--receipt', nargs=3, metavar=('VARIANT', 'PHASE', 'RAW'))
    mode.add_argument('--unpack', nargs=4, metavar=('LOG', 'VARIANT', 'PHASE', 'OUTPUT'))
    mode.add_argument('--score', nargs='+', metavar='PATH')
    args = parser.parse_args()
    if args.receipt:
        receipt(*args.receipt)
    elif args.unpack:
        unpack(*args.unpack)
    else:
        fixtures, phase, *paths = args.score
        print(json.dumps(evaluate(Path(fixtures), phase, [Path(p) for p in paths]), ensure_ascii=False, indent=2))
