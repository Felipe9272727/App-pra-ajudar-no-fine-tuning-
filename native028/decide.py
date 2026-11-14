"""Apply the preregistered monotone gates; never select using NLL."""
from inference import *


def compare(parent,candidate):
    ps={(r['kind'],r['id'],r['thinking']):r for r in parent['rows']}
    cs={(r['kind'],r['id'],r['thinking']):r for r in candidate['rows']};assert set(ps)==set(cs)
    lost=[];gained=[]
    for key,p in ps.items():
        c=cs[key]
        if key[0]=='code':
            assert len(p['case_passed'])==len(c['case_passed'])
            for i,(a,b) in enumerate(zip(p['case_passed'],c['case_passed'])):
                if a and not b:lost.append([*key,i])
                if b and not a:gained.append([*key,i])
        elif p['correct'] and not c['correct']:lost.append(list(key))
    summary_p=summarize(parent);summary_c=summarize(candidate)
    task_gain=sum(v['code_tasks'] for v in summary_c.values())-sum(v['code_tasks'] for v in summary_p.values())
    no_mode_task_loss=all(summary_c[k]['code_tasks']>=v['code_tasks'] for k,v in summary_p.items())
    return {'eligible':task_gain>0 and not lost and no_mode_task_loss,'completed_code_task_gain':task_gain,
        'lost_parent_correct_cases_or_controls':lost,'gained_code_cases':gained,'no_mode_task_loss':no_mode_task_loss}


def main():
    verify_stage('evaluation');assert not (H/'selection.json').exists(),'Selection already frozen'
    variants={v:read('reports/validation_'+v+'.json') for v in ['original','parent','sft_final','policy_final']}
    assert all(r.get('status')=='complete' for r in variants.values())
    checks={v:compare(variants['parent'],variants[v]) for v in ['sft_final','policy_final']}
    def rank(v):
        s=summarize(variants[v]);return (sum(x['code_tasks'] for x in s.values()),sum(x['cases'] for x in s.values()),-sum(x['tokens'] for x in s.values()),v=='sft_final')
    eligible=[v for v in checks if checks[v]['eligible']]
    winner=max(eligible,key=rank) if eligible else None
    save('selection.json',{'selected':winner,'checks':checks,'final_gate_open':winner is not None,
        'selected_parent_unchanged':True,'promotion_pending_fresh_final':winner is not None,
        'all_summaries':{v:summarize(r) for v,r in variants.items()}})
    print('SELECTION028',winner,flush=True)
if __name__=='__main__':main()
