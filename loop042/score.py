"""Score identical prompts across runs while keeping keys out of the model process."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_cpu.sandbox import evaluate as judge_code


def text_key(text):
    return ' '.join(text.casefold().strip(' \n\t`*.').split())


def grade(text, key):
    kind = key['type']
    if kind == 'ifbench':
        from evaluation_lib import InputExample, test_instruction_following_strict
        row = key['row']
        result = test_instruction_following_strict(InputExample(**row), {row['prompt']: text})
        return bool(result.follow_all_instructions), {}
    if kind == 'code':
        result = judge_code(text, key)
        bits = result.get('case_passed', [False] * result['total'])
        return bool(result['all_passed']), {'passed_cases': result['passed'],
            'total_cases': result['total'], 'case_passed': bits, 'category': result.get('category')}
    if kind == 'text':
        return any(text_key(text) == text_key(expected) for expected in key['expected']), {}
    if kind == 'legacy_text':
        value = text.strip().lower().rstrip('.!?。').strip()
        return value in [str(a).strip().lower() for a in key['expected']], {}
    pattern = r'[A-J]' if kind == 'letter' else r'\d{1,3}'
    lines = re.findall(rf'(?im)^\s*(?:\*\*)?Answer\s*:\s*({pattern})\b', text)
    if not lines:
        lines = re.findall(rf'\\boxed\{{\s*({pattern})\s*\}}', text)
    if not lines:
        only = re.fullmatch(rf'\s*({pattern})[.]?\s*', text, re.IGNORECASE)
        lines = [only[1]] if only else []
    picked = lines[-1].upper() if lines else None
    if kind == 'integer' and picked is not None:
        picked = int(picked)
    return picked == key['expected'], {'extracted': picked}


def score(raw_path, prompts, grading):
    raw = [json.loads(line) for line in raw_path.read_text().splitlines()]
    assert [r['id'] for r in raw] == [r['id'] for r in prompts], raw_path
    scored = []
    for row in raw:
        item = {k: row[k] for k in ('id', 'group', 'seconds')}
        if 'error' in row:
            item.update(correct=False, error=row['error'], tokens=0)
        else:
            answer = row['answer']
            ok, detail = grade(answer['text'], grading[row['id']])
            item.update(correct=ok, **detail, final=answer['text'], tokens=answer['tokens'],
                reasoning_tokens=answer['reasoning_tokens'], response_tokens=answer['response_tokens'],
                first_token_seconds=answer['first_token_seconds'], finish_reason=answer['finish_reason'],
                generated_ids=answer['generated_ids'])
        scored.append(item)
    return scored


def summarize(items, baseline):
    groups = defaultdict(list)
    before = {r['id']: r for r in baseline}
    for row in items:
        groups[row['group']].append(row)
    out = {}
    for group, rows in groups.items():
        secs = sum(r['seconds'] for r in rows)
        tokens = sum(r['tokens'] for r in rows)
        correct = sum(r['correct'] for r in rows)
        head = [r['first_token_seconds'] for r in rows if r.get('first_token_seconds') is not None]
        out[group] = {'correct': correct, 'count': len(rows), 'seconds': secs, 'tokens': tokens,
            'correct_per_minute': correct*60/secs, 'correct_per_1000_tokens': correct*1000/tokens if tokens else None,
            'median_first_token_seconds': statistics.median(head) if head else None,
            'wins': sum(r['correct'] and not before[r['id']]['correct'] for r in rows),
            'losses': sum(not r['correct'] and before[r['id']]['correct'] for r in rows),
            'identical_ids': sum(r.get('generated_ids') == before[r['id']].get('generated_ids') for r in rows),
            'passed_cases': sum(r.get('passed_cases',0) for r in rows),
            'total_cases': sum(r.get('total_cases',0) for r in rows),
            'errors': sum('error' in r for r in rows), 'hit_limit': sum(r.get('finish_reason')=='length' for r in rows)}
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('fixtures', type=Path)
    p.add_argument('runs', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    cases = json.loads((args.fixtures/'prompts.json').read_text())
    keys = json.loads((args.fixtures/'grading.json').read_text())
    baseline = score(args.runs/'previous.jsonl', cases, keys)
    totals = {}
    for path in sorted(args.runs.glob('*.jsonl')):
        data = score(path, cases, keys)
        totals[path.stem] = summarize(data, baseline)
        (args.output/f'{path.stem}-scored.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    assert totals['window'].keys() == totals['previous'].keys()
    for result in totals['window'].values():
        assert result['count'] == result['identical_ids'] and not result['errors'], result
    (args.output/'comparison.json').write_text(json.dumps(totals, indent=2)+'\n')
