"""Separate observed delivery/contract failures from semantic code errors."""
import json,collections
from pathlib import Path
H=Path(__file__).resolve().parent

def read(p):return json.loads((H/p).read_text())
def failure(row):
    if row.get('all_passed'):return 'passed_all_cases'
    if not row['thinking_closed']:return 'unfinished_thinking'
    if row.get('hit_limit'):return 'generation_limit_after_thinking_closure'
    return row.get('category','unknown')
def main():
    variants={v:read(f'reports/validation_{v}.json') for v in ['original','parent','sft_final','policy_final']}
    assert all(r['status']=='complete' for r in variants.values())
    parent={(r['id'],r['thinking']):r for r in variants['parent']['rows'] if r['kind']=='code'}
    result={'scope':'post-hoc description, never used to change judges, weights or selection',
        'warning':'192-token thinking budget tests short-budget delivery; not app Extenso or full long reasoning. A completed answer versus unfinished thought is a usability gain, not proof of stronger latent reasoning.',
        'variants':{}}
    for v,report in variants.items():
        codes=[r for r in report['rows'] if r['kind']=='code']
        counts={str(t):dict(collections.Counter(failure(r) for r in codes if r['thinking']==t)) for t in [False,True]}
        wins=[];losses=[]
        for r in codes:
            old=parent[(r['id'],r['thinking'])]
            if r['all_passed'] and not old['all_passed']:
                wins.append({'id':r['id'],'thinking':r['thinking'],'parent_failure_mode':failure(old),'parent_tokens':old['tokens'],'candidate_tokens':r['tokens']})
            if old['all_passed'] and not r['all_passed']:losses.append({'id':r['id'],'thinking':r['thinking'],'candidate_failure_mode':failure(r)})
        result['variants'][v]={'failure_categories':counts,'completed_task_gains_vs_parent':wins,'completed_task_losses_vs_parent':losses}
    replay=[s for g in read('reports/policy_groups.json') for s in g['replay_stats']]
    n=sum(len(r['replay_logp']) for r in replay)
    result['policy_replay_numerics']={'scored_tokens':n,
        'mean_abs_logp_mismatch_weighted':sum(r['mean_abs_logp_mismatch']*len(r['replay_logp']) for r in replay)/n if n else None,
        'max_abs_logp_mismatch':max((r['max_abs_logp_mismatch'] for r in replay),default=None),
        'clipped_fraction_weighted':sum(r['ratio_clipped_fraction']*len(r['replay_logp']) for r in replay)/n if n else None,
        'note':'cached additive behavior vs uncached BF16 full-prefix replay; numerical discrepancy is measured, not absent'}
    (H/'reports/error_modes.json').write_text(json.dumps(result,indent=2)+'\n');print('ERROR_MODES028_RECORDED_NO_NEW_INFERENCE')
if __name__=='__main__':main()
