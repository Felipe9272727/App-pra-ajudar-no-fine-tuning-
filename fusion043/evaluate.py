"""Prepare unseen prompts, then score the three paired generation runs."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from loop042.score import score, summarize

HERE = Path(__file__).resolve().parent


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare(folder):
    prompts, keys = [], {}

    def add(name, group, text, key, response, reasoning=0):
        assert name not in keys
        prompts.append({'id': name, 'group': group, 'prompt': text,
                        'options': {'thinking': bool(reasoning), 'reasoning_tokens': reasoning,
                                    'response_tokens': response, 'context_tokens': 16384}})
        keys[name] = key

    legacy = ROOT / 'loop042' / 'data'
    for row in json.loads((legacy / 'validation_code.json').read_text()):
        add(row['id'], 'Código029', row['prompt'], {'type': 'code', 'cases': row['cases']}, 128)
    for row in json.loads((legacy / 'legacy_general.json').read_text()):
        add(row['id'], 'Controles029', row['prompt'], {'type': 'legacy_text', 'expected': row['answers']}, 48)

    add('G043/edges', 'Código043',
        'Write only Python code for solve(xs). Return the number of adjacent pairs in xs whose two integers are both negative. Overlapping pairs count separately.',
        {'type': 'code', 'cases': [{'args': [xs], 'expected': n} for xs, n in [
            ([], 0), ([-1], 0), ([-1, -2, -3], 2), ([-1, 0, -2, -3, 5], 1), ([0, 1, 3], 0)]]}, 96)
    add('G043/encoders', 'Código043',
        'Implement Python solve(encoders). The argument maps text names to integer scores. Return names with score strictly above zero, ordered by score descending and then by name ascending. Return only code.',
        {'type': 'code', 'cases': [{'args': [xs], 'expected': n} for xs, n in [
            ({}, []), ({'c': 3, 'b': 3, 'a': 4, 'z': 0}, ['a', 'b', 'c']),
            ({'null': -1, 'x': 0}, []), ({'zz': 2, 'ab': 7}, ['ab', 'zz']),
            ({'b': 1, 'a': 1}, ['a', 'b'])]]}, 96)
    add('G043/pt-math', 'Raciocínio043',
        'Havia 11 livros. Foram doados 4 e depois chegaram 8. Quantos livros ficaram? Na resposta final, escreva só o número.',
        {'type': 'text', 'expected': ['15']}, 24, 32)
    add('G043/en-order', 'Raciocínio043',
        'The red box is heavier than the blue box. The green box is lighter than the blue box. Which box is heaviest? Give only the color in the final answer.',
        {'type': 'text', 'expected': ['red']}, 24, 32)
    add('G043/echo-code', 'Texto043',
        'Copy the identifier between backticks exactly, without backticks or other text: `StringSet`.',
        {'type': 'text', 'expected': ['StringSet']}, 24)
    add('G043/echo-pt', 'Texto043',
        'Escreva só esta frase exata, sem aspas: "As encoders são úteis?"',
        {'type': 'text', 'expected': ['As encoders são úteis?']}, 24)

    calibration = json.loads((HERE / 'data' / 'calibration.json').read_text())
    assert not {row['prompt'] for row in calibration}.intersection(row['prompt'] for row in prompts)
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'prompts.json', prompts)
    write(folder / 'grading.json', keys)


def compare(fixtures, runs, report):
    prompts = json.loads((fixtures / 'prompts.json').read_text())
    keys = json.loads((fixtures / 'grading.json').read_text())
    variants = {n: score(runs / f'{n}.jsonl', prompts, keys) for n in ('base', 'lexicon', 'fusion')}
    data = {}
    for name, rows in variants.items():
        groups = summarize(rows, variants['base'])
        assert not any(v['errors'] for v in groups.values()), (name, groups)
        data[name] = {
            'correct': sum(row['correct'] for row in rows),
            'count': len(rows),
            'seconds': sum(row['seconds'] for row in rows),
            'groups': groups,
            'different_text_from_base': sum(a['final'] != b['final'] for a, b in zip(rows, variants['base'])),
            'different_text_from_lexicon': sum(a['final'] != b['final'] for a, b in zip(rows, variants['lexicon'])),
        }
        write(report / f'{name}-scored.json', rows)
    write(report / 'comparison.json', data)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('fixtures', type=Path)
    parser.add_argument('--runs', type=Path)
    args = parser.parse_args()
    if args.runs is None:
        prepare(args.fixtures)
    else:
        compare(args.fixtures, args.runs, HERE / 'reports')
