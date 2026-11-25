"""Validate and join paired shard outputs in the frozen prompt order."""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('prompts', type=Path)
p.add_argument('parts', type=Path)
p.add_argument('output', type=Path)
args = p.parse_args()
cases = json.loads(args.prompts.read_text())
shards = sorted(args.parts.glob('shard-*'))
assert len(shards) == 6, shards
args.output.mkdir(parents=True, exist_ok=True)
expected = {case['id']: case['group'] for case in cases}
for variant in ['previous','window','static','adaptive','hybrid','combined']:
    rows = {}
    for shard in shards:
        file = shard/f'{variant}.jsonl'
        for line in file.read_text().splitlines():
            item = json.loads(line)
            assert item['id'] not in rows, item['id']
            assert expected.get(item['id']) == item['group'], item['id']
            rows[item['id']] = item
    assert rows.keys() == expected.keys(), (variant,expected.keys()-rows.keys())
    ordered = (json.dumps(rows[case['id']], ensure_ascii=False) for case in cases)
    (args.output/f'{variant}.jsonl').write_text('\n'.join(ordered)+'\n')
