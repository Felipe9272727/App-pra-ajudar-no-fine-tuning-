"""Once-only new custom pilot after retention gate, four fixed model variants."""
import sys,json,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from balanced016.train import HERE,e,torch,verify_frozen,save
from balanced016.restore import load_candidate,load_e
from reasoning.runtime_helpers import load as load_principal
from balanced016.judge import evaluate as judge

@torch.inference_mode()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--variant',choices=['original','principal','E','candidate'],required=True);args=ap.parse_args()
    verify_frozen();gate=json.loads((HERE/'gate.json').read_text());assert gate['passed'],'Do not consume sealed questions after failed screen'
    if args.variant=='original':model,meta=e.cr.load('original');tok=e.cr.tokenizer();identity='original'
    elif args.variant=='principal':model,tok,_,meta=load_principal();identity='principal46f6697'
    else:model,tok,meta,m=load_e() if args.variant=='E' else load_candidate();identity=m['stream_sha256']
    assert model.generation_config.eos_token_id==248044
    for role,file in [('code','validation_code.json'),('controls','validation_controls.json')]:
        rows=json.loads((HERE/file).read_text());path=HERE/('fresh_'+role+'_'+args.variant+'.json')
        report=json.loads(path.read_text()) if path.exists() else {'status':'running','variant':args.variant,'checkpoint_identity':identity,'metadata':meta,'rows':[],
          'protocol':{'custom_pilot_not_official_benchmark':True,'greedy':True,'seed':0,'thinking':False,'cpu_threads':4,'max_new_tokens':320 if role=='code' else 64,'solutions_in_generation_input':False,'tests_in_generation_input':False,'candidate_frozen_before_all_validation_outputs':True}}
        assert report['checkpoint_identity']==identity
        if report['status']=='complete':continue
        seen={r['id'] for r in report['rows']}
        for row in rows:
            if row['id'] in seen:continue
            question=row['prompt'] if role=='code' else row['question']
            out=e.cr.generate(model,tok,question,max_tokens=320 if role=='code' else 64);out.pop('trace',None)
            score=judge(out['output'],row) if role=='code' else {'correct':e.cr.grade(out['output'],row)[0]}
            report['rows'].append({'id':row['id'],**out,**score});e.cr.atomic_json(path,report)
            save('status.json',{'status':'fresh_'+role+'_'+args.variant,'completed_in_phase':len(report['rows']),'model_process_active':True,'checkpoint_promoted':False,'process_continues_in_background':False})
            print('FRESH',args.variant,role,row['id'],score.get('all_passed',score.get('correct')),flush=True)
        report.update(status='complete',total=len(rows),correct=sum(r['all_passed'] if role=='code' else r['correct'] for r in report['rows']));e.cr.atomic_json(path,report)
    save('status.json',{'status':'fresh_variant_complete','variant':args.variant,'model_process_active':False,'checkpoint_promoted':False,'process_continues_in_background':False})
if __name__=='__main__':main()
