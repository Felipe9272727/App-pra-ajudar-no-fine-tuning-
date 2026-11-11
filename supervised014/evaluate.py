"""Two benchmark subsets, one fixed candidate, same inference for each model."""
import argparse,json
from core import *
from judge import evaluate

@torch.inference_mode()
def main(kind,role):
    frozen();model,tok,meta=load_variant(kind);path=HERE/(role+'_'+kind+'.json')
    report=json.loads(path.read_text()) if path.exists() else {'kind':kind,'role':role,'metadata':meta,
        'frozen_sha256':sha(HERE/'frozen.json'),'rows':[],
        'protocol':{'max_new_tokens':320,'greedy':True,'thinking':False,'seed':0,'threads':4,
                    'reference_solution_in_generation_input':False,'test_code_in_generation_input':False,
                    'public_examples_in_official_statement':True,'candidate_programs_per_task':1}}
    assert report['frozen_sha256']==sha(HERE/'frozen.json')
    assert report['metadata'].get('patch_sha256')==meta.get('patch_sha256')
    if report.get('status')=='complete':print('COMPLETE_SKIP',kind,role,flush=True);return
    rows=json.loads((HERE/(role+'.json')).read_text()) if role in ['taught','transfer'] else json.loads((ROOT/'review013/controls.json').read_text())
    seen={r['id'] for r in report['rows']}
    for row in rows:
        if row['id'] in seen:continue
        # Explicitly pass a single statement string, never a reference/test object.
        prompt=row['question'] if role=='controls' else row['prompt']
        out=e.cr.generate(model,tok,prompt,max_tokens=64 if role=='controls' else 320);out.pop('trace',None)
        if role=='controls':
            exact,_=e.cr.grade(out['output'],row);score={'correct':exact}
        else:score=evaluate(out['output'],row)
        report['rows'].append({'id':row['id'],**out,**score});e.cr.atomic_json(path,report)
        print('EVAL',role,kind,row['id'],score.get('all_passed',score.get('correct')),score.get('category',''),round(out['seconds'],2),flush=True)
    if role=='controls':
        report['correct']=sum(r['correct'] for r in report['rows'])
        report['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)
    else:
        report['tasks_passed']=sum(r['all_passed'] for r in report['rows'])
        report['test_groups_passed']=sum(r['passed'] for r in report['rows'])
        report['test_groups_total']=sum(r['total'] for r in report['rows'])
    report['status']='complete';report['total']=len(rows);e.cr.atomic_json(path,report)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['original','parent','edited']);p.add_argument('role',choices=['taught','transfer','controls']);a=p.parse_args();main(a.kind,a.role)
