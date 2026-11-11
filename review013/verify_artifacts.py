"""Fail closed on mismatched saved outputs; no model inference or score repair."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def read(p):return json.loads((HERE/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    frozen=read('frozen.json')
    for name,h in frozen.items():assert sha(ROOT/name)==h,name
    expected=[r for r in read('validation.json') if r['variant'] in [0,9]]
    ids=[r['id'] for r in expected];control_ids=[r['id'] for r in read('controls.json')]
    for kind in ['original','parent','loop','joint']:
        report=read('screen_'+kind+'.json');assert report['status']=='complete'
        assert [r['id'] for r in report['rows']]==ids
        assert report['frozen_sha256']==sha(HERE/'frozen.json')
        assert report['tasks_passed']==sum(r['all_passed'] for r in report['rows'])
        assert report['cases_passed']==sum(r['passed'] for r in report['rows'])
        assert report['cases_total']==160
        for row,task in zip(report['rows'],expected):
            assert row['total']==len(task['cases'])==20
            assert row['passed']==sum(row['case_passed'])
            assert row['all_passed']==all(row['case_passed'])
        c=read('controls_'+kind+'.json');assert c['status']=='complete'
        assert c['frozen_sha256']==sha(HERE/'frozen.json')
        assert [r['id'] for r in c['rows']]==control_ids
        assert c['correct']==sum(r['correct'] for r in c['rows'])
    fit=read('fit.json')
    for kind,v in fit['candidates'].items():assert sha(HERE/'checkpoints'/(kind+'.pt'))==v['sha256']
    selected=read('selection.json');assert not selected['checkpoint_promoted']
    assert sha(ROOT/'rsi100/checkpoints/best.pt')=='46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'
    if selected['status']=='complete_both_rejected_screen':
        assert not list(HERE.glob('test_*.json')),'unexpected final test outputs'
        assert not list(HERE.glob('full_validation_*.json')),'unexpected full validation outputs'
    audit={'status':'all_saved_results_consistent','variants':4,'screen_problems_per_variant':8,
           'screen_cases_per_variant':160,'controls_per_variant':12,'parent_retained':True,
           'frozen_sha256':sha(HERE/'frozen.json'),'score_repair_performed':False}
    (HERE/'artifact_verification.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))
if __name__=='__main__':main()
