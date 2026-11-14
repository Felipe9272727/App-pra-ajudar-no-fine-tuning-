"""Fixed fresh + known-retention gates; no selection from NLL."""
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
    verify_stage('evaluation');assert not (H/'selection.json').exists(),'Decision already frozen'
    names=['original','parent']+[f'epoch{i:02d}' for i in range(1,5)]
    reports={v:read('reports/validation_'+v+'.json') for v in names}
    legacy={v:read('reports/legacy_'+v+'.json') for v in names if v!='original'}
    assert all(r['status']=='complete' for r in list(reports.values())+list(legacy.values()))
    matched=legacy['parent']['historical_parent_reference_match'];checks={}
    for v in names[2:]:
        fresh=compare(reports['parent'],reports[v]);known=compare(legacy['parent'],legacy[v])
        retained=not known['lost_parent_correct_cases_or_controls'] and known['no_mode_task_loss']
        checks[v]={'eligible':fresh['eligible'] and retained and matched,'fresh':fresh,'known_retention':known,
            'all_known_retained':retained,'legacy_parent_replay_matches_historical':matched}
    def rank(v):
        s=reports[v]['summary'];return (sum(x['code_tasks'] for x in s.values()),sum(x['cases'] for x in s.values()),-sum(x['tokens'] for x in s.values()),-int(v[-2:]))
    eligible=[v for v,c in checks.items() if c['eligible']];winner=max(eligible,key=rank) if eligible else None
    save('selection.json',{'selected':winner,'checks':checks,'final_gate_open':winner is not None,
        'historical_parent_reference_match':matched,'principal_file_unchanged':True,
        'all_summaries':{v:r['summary'] for v,r in reports.items()},
        'legacy_summaries':{v:r['summary'] for v,r in legacy.items()}})
    print('SELECTION029',winner,flush=True)
if __name__=='__main__':main()
