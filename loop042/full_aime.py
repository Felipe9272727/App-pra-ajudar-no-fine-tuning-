"""Compare both endpoints of the experiment on all 30 AIME25 items."""
import argparse
import json
from pathlib import Path

from score import score, summarize

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--score', action='store_true')
args = parser.parse_args()
source = json.loads(args.source.read_text())['rows']
assert len(source) == 30
args.output.mkdir(parents=True, exist_ok=True)
cases, keys = [], {}
for item in source:
    row = item['row']
    key = f"AIME25/{row['id']}"
    cases.append({'id':key, 'group':'AIME25',
        'prompt':row['problem']+'\n\nEnd with a separate line: Answer: N, where N is your final integer.',
        'options':{'thinking':True,'reasoning_tokens':48,'response_tokens':24,'context_tokens':16384}})
    keys[key] = {'type':'integer','expected':int(row['answer'])}

if not args.score:
    (args.output/'prompts.json').write_text(json.dumps(cases)+'\n')
else:
    runs = {v: score(args.output/f'{v}.jsonl',cases,keys) for v in ['previous','combined']}
    print(json.dumps({v:{'summary':summarize(rows,runs['previous']),'rows':rows}
        for v,rows in runs.items()}, indent=2))
