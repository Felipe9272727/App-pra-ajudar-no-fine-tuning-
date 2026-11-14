"""Descriptive paired family sign test; two modes are not independent tasks."""
import json,math
from pathlib import Path
H=Path(__file__).resolve().parent

def read(p):return json.loads((H/p).read_text())
def main():
    parent=read('reports/validation_parent.json');assert parent['status']=='complete'
    ps={(r['id'],r['thinking']):r for r in parent['rows'] if r['kind']=='code'}
    output={'sampling':'greedy one fixed output per prompt; no sampled pass@k',
        'unit':'four problem families, grouping the two thinking modes',
        'limitation':'n=4 families; two modes share each problem. Minimum two-sided exact sign p=.125. No adequately powered superiority claim.',
        'candidates':{}}
    for variant in ['original','sft_final','policy_final']:
        cand=read('reports/validation_'+variant+'.json');assert cand['status']=='complete'
        cs={(r['id'],r['thinking']):r for r in cand['rows'] if r['kind']=='code'};assert set(cs)==set(ps)
        families=[]
        for id in sorted({key[0] for key in ps}):
            p=sum(int(ps[(id,t)]['all_passed']) for t in [False,True]);c=sum(int(cs[(id,t)]['all_passed']) for t in [False,True])
            families.append({'id':id,'parent_completed_modes':p,'candidate_completed_modes':c,'difference':c-p})
        pos=sum(r['difference']>0 for r in families);neg=sum(r['difference']<0 for r in families);n=pos+neg
        pvalue=min(1.,2*sum(math.comb(n,k) for k in range(min(pos,neg)+1))/(2**n)) if n else 1.
        output['candidates'][variant]={'families':families,'improved':pos,'regressed':neg,'ties':4-n,'two_sided_exact_sign_p':pvalue}
    (H/'reports/paired_uncertainty.json').write_text(json.dumps(output,indent=2)+'\n')
    print('UNCERTAINTY028_RECORDED_NO_GENERATION')
if __name__=='__main__':main()
