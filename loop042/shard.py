"""Assign the same tasks and order to each variant on a single runner."""
import argparse
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('shard', type=int)
p.add_argument('count', type=int)
args = p.parse_args()
assert 0 <= args.shard < args.count
cases = json.loads(args.input.read_text())
bins = [[] for _ in range(args.count)]
sizes = [0] * args.count

def work(case):
    options = case['options']
    return len(case['prompt']) + 11*(options['reasoning_tokens'] + options['response_tokens'])

for case in sorted(cases, key=work, reverse=True):
    i = sizes.index(min(sizes))
    bins[i].append(case)
    sizes[i] += work(case)
selected = {case['id'] for case in bins[args.shard]}
print(json.dumps([case for case in cases if case['id'] in selected]))
