"""Paired coding-superiority metric. Missing 4B results never become a score."""
import math
import numpy as np

def summarize(rows):
    assert rows and len({r['id'] for r in rows})==len(rows)
    n=len(rows);solved=sum(bool(r['all_passed']) for r in rows)
    return {'problems':n,'fully_solved':solved,'problem_pass_at_1':solved/n,
        'cases_passed':sum(r['passed'] for r in rows),'cases_total':sum(r['total'] for r in rows)}

def compare(liquid,reference=None,*,fresh=False,controls_preserved=False,bootstrap_samples=20000):
    result={'metric':'Delta4B_pp','liquid':summarize(liquid['rows']),
        'status':'unmeasured_missing_4b_reference','delta_pp':None,'coding_superiority_confirmed':False}
    if reference is None:return result
    assert liquid['protocol']==reference['protocol'],'Inference/evaluation protocol mismatch'
    a={r['id']:bool(r['all_passed']) for r in liquid['rows']};b={r['id']:bool(r['all_passed']) for r in reference['rows']}
    assert set(a)==set(b),'Problem IDs mismatch'
    assert reference['model_id']=='Qwen/Qwen3.5-4B' and reference.get('model_revision'),'Not a pinned actual 4B baseline'
    keys=sorted(a);d=np.array([int(a[k])-int(b[k]) for k in keys]);n=len(d)
    wins=int((d==1).sum());losses=int((d==-1).sum());discordant=wins+losses
    p=sum(math.comb(discordant,k) for k in range(wins,discordant+1))/2**discordant if discordant else 1.
    rng=np.random.default_rng(2026110511);means=[]
    for start in range(0,bootstrap_samples,1000):
        batch=min(1000,bootstrap_samples-start);means.extend(d[rng.integers(0,n,size=(batch,n))].mean(1).tolist())
    low,high=np.quantile(means,[.025,.975])*100
    result.update(status='measured',reference=summarize(reference['rows']),delta_pp=float(d.mean()*100),
        paired_wins=wins,paired_losses=losses,ci95_pp=[float(low),float(high)],one_sided_p=float(p),
        fresh_problem_pairs=fresh,controls_preserved=controls_preserved,
        coding_superiority_confirmed=bool(fresh and n>=100 and controls_preserved and low>0 and p<.05))
    return result
