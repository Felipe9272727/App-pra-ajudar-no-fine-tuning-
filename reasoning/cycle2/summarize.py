"""Compact paired findings without confusing decoding changes and weight gains."""
import collections
import hashlib
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
import stdio_judge_v2 as judge

def read(name):return json.loads((HERE/name).read_text())
summary={'weight_trial':read('trial_006.json'),
    'scoring_audit':{k:{a:b for a,b in v.items() if a!='rows'} for k,v in read('judge_audit.json')['variants'].items()},
    'decoding_diagnostic':{},'comparisons_are_observed_development_only':True,
    'reference_answers_in_inference':False,'backward_passes':0}
for var in ['original','liquid']:
    data=read(f'thinking_{var}.json');assert data['status']=='complete'
    historical={r['id']:r for r in json.loads((ROOT/f'benchmarks/reasoning_20261105/results_{var}.json').read_text())['rows']}
    stats={};rows=[]
    for row in data['rows']:
        strict_final=not row['thinking'] or (row['thinking_closed'] and bool(row['output'].rsplit('</think>',1)[-1].strip()))
        record={'id':row['id'],'thinking':row['thinking'],'passed':row['all_passed'],
            'final_segment_available':strict_final,'completed_and_correct':strict_final and row['all_passed'],
            'new_tokens':row['new_tokens'],'cap':row['hit_limit'],'seconds':row['seconds']}
        if not row['thinking']:
            old=historical[row['id']]
            record['same_historical_prefix_or_completed_output']=row['output'].startswith(old['output']) if old['hit_limit'] else row['output']==old['output']
        if row['id'].startswith('lcb:'):
            oracle=json.loads((ROOT/'benchmarks/reasoning_20261105/oracles.json').read_text())[row['id']]
            corrected=judge.evaluate(row['output'],oracle)
            record.update(audit_v2_passed=corrected['all_passed'],audit_v2_category=corrected['category'])
        rows.append(record)
    for thinking in [False,True]:
        rs=[x for x in rows if x['thinking']==thinking]
        stats[str(thinking)]={'tasks':len(rs),'raw_correct':sum(r['passed'] for r in rs),
            'final_segments_available':sum(r['final_segment_available'] for r in rs),
            'completed_and_correct':sum(r['completed_and_correct'] for r in rs),
            'capped':sum(r['cap'] for r in rs),'tokens':sum(r['new_tokens'] for r in rs),
            'seconds':sum(r['seconds'] for r in rs)}
    summary['decoding_diagnostic'][var]={'aggregate':stats,'rows':rows}
for var in ['original','parent','target']:
    path=HERE/('development_original.json' if var=='original' else f'trial_006_{var}_full.json')
    if path.exists():
        r=json.loads(path.read_text());assert r['status']=='complete'
        summary.setdefault('development',{})[var]={'tasks':sum(x['all_passed'] for x in r['rows']),
            'cases':sum(x['passed'] for x in r['rows']),'total_cases':sum(x['total'] for x in r['rows']),
            'controls':sum(r['control_bits']),'anchor_nll':r['anchor_nll']}
if (HERE/'selection.json').exists():summary['selection']=read('selection.json')
if (HERE/'trial_007.json').exists():summary['router_trial']=read('trial_007.json')
if (HERE/'router_runtime_audit.json').exists():
    audit=read('router_runtime_audit.json')
    summary['mHC_stream_audit']={'router_count':len(audit['routers']),
        'all_streams_equal_in_measured_inputs':audit['all_streams_equal_in_measured_inputs'],
        'router_calls':sum(x['observations'] for x in audit['routers'].values()),
        'input_positions':sum(x['positions'] for x in audit['routers'].values())}
for var in ['original','liquid']:
    path=HERE/f'thinking1024_{var}.json'
    if path.exists():
        data=read(path.name);assert data['status']=='complete'
        rows=[]
        for r in data['rows']:
            final=r['thinking_closed'] and bool(r['output'].rsplit('</think>',1)[-1].strip())
            rows.append({'id':r['id'],'new_tokens':r['new_tokens'],'capped':r['hit_limit'],
                'final_segment':final,'completed_and_correct':final and r['all_passed'],
                'reused_completed_512_output':r['reused_completed_512_output'],
                'same_512_prefix':r['same_512_prefix']})
        summary.setdefault('budget1024',{})[var]={'rows':rows,'tasks':len(rows),
            'completed_and_correct':sum(r['completed_and_correct'] for r in rows),
            'capped':sum(r['capped'] for r in rows)}
summary['preserved_legacy_frozen_hashes']=all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v
    for n,v in json.loads((ROOT/'benchmarks/reasoning_20261105/frozen.json').read_text())['files'].items())
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['weight_trial']},indent=2))
