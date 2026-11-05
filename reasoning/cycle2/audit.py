"""Rescore identical saved code with a separate, explicit harness correction."""
import json
from pathlib import Path
import stdio_judge_v2 as judge

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
SOURCE=ROOT/'benchmarks/reasoning_20261105'
oracles=json.loads((SOURCE/'oracles.json').read_text())
report={'purpose':'measurement audit only; no primary scores overwritten',
    'changes':['allow ordinary underscore locals','expose iter/next/bytes/bytearray builtins'],
    'generation_repeated':False,'gold_answers_changed':False,'variants':{}}
for variant in ['original','liquid']:
    rows=[]
    for old in json.loads((SOURCE/f'results_{variant}.json').read_text())['rows']:
        if not old['id'].startswith('lcb:'):continue
        scored=judge.evaluate(old['output'],oracles[old['id']])
        rows.append({'id':old['id'],'old_passed':old['passed'],'old_category':old['category'],
            'old_detail':old.get('detail'),**scored})
    report['variants'][variant]={'rows':rows,'tasks':sum(r['all_passed'] for r in rows),
        'cases':sum(r['passed'] for r in rows),'changed_case_count':sum(r['passed']-r['old_passed'] for r in rows)}
    (HERE/'judge_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print('JUDGE_AUDIT',variant,report['variants'][variant]['tasks'],report['variants'][variant]['cases'],flush=True)
