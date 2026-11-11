"""Check saved scores/data/weights without inference or repairing results."""
import gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((HERE/n).read_text())
def main():
    for path,h in read('frozen.json').items():assert sha(ROOT/path)==h,path
    fh=sha(HERE/'frozen.json');teach=read('teaching.json')
    assert sha(HERE/'checkpoints/candidate.pt')==teach['candidate_sha256']
    assert sha(ROOT/'rsi100/checkpoints/best.pt')==teach['parent_sha256']
    assert teach['changed_tensors']==['model.language_model.layers.31.mlp.down_proj.weight']
    assert teach['parent_tensors_checked']==699
    for role in ['taught','transfer','controls']:
        rows=read(role+'.json') if role!='controls' else json.loads((ROOT/'review013/controls.json').read_text())
        for kind in ['original','parent','edited']:
            r=read(role+'_'+kind+'.json');assert r['status']=='complete'
            assert r['frozen_sha256']==fh
            assert [x['id'] for x in r['rows']]==[x['id'] for x in rows]
            if kind=='edited':assert r['metadata']['patch_sha256']==teach['candidate_sha256']
            if role=='controls':assert r['correct']==sum(x['correct'] for x in r['rows'])
            else:
                assert r['tasks_passed']==sum(x['all_passed'] for x in r['rows'])
                for x,y in zip(r['rows'],rows):
                    assert x['passed']==sum(x['case_passed'])
                    assert x['total']==len(y['tests'])==len(x['case_passed'])
                    assert x['all_passed']==all(x['case_passed'])
    human={r['task_id']:r for r in [json.loads(l) for l in gzip.decompress((HERE/'sources/humaneval.jsonl.gz').read_bytes()).decode().splitlines()]}
    mbpp={r['task_id']:r for r in read('sources/mbpp.json')}
    for row in read('taught.json'):
        assert row['tests']==[human[row['id']]['test']]
        assert row['canonical_solution']==human[row['id']]['canonical_solution']
    for row in read('transfer.json'):
        old=mbpp[int(row['id'].split('/')[-1])];assert row['tests']==old['test_list'];assert row['solution']==old['code']
    expected={'human_'+r['id'].split('/')[-1]+'.pt' for r in read('taught.json')}|{'language.pt'}
    assert {p.name for p in (HERE/'states').glob('*.pt')}==expected
    report={'status':'all_artifacts_consistent','models':3,'taught_tasks_per_model':8,'transfer_tasks_per_model':8,
       'controls_per_model':12,'official_golds_and_tests_changed':False,'candidate_sha256':teach['candidate_sha256'],
       'parent_retained':True,'data_used_for_editing':'8 HumanEval programs plus zero-target language-anchor protection, no MBPP references'}
    (HERE/'artifact_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
