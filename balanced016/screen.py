"""Candidate-only cached generation; historical baselines and judges stay unchanged."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from balanced016.train import HERE,save,verify_frozen,e,torch
from balanced016.restore import load_candidate
from supervised014.judge import evaluate as judge

@torch.inference_mode()
def main():
    verify_frozen();training=json.loads((HERE/'training_complete.json').read_text());cfg=json.loads((HERE/'config.json').read_text())
    model,tok,meta,m=load_candidate();assert m['stream_sha256']==training['checkpoint_stream_sha256']
    meta.update(checkpoint_stream_sha256=m['stream_sha256'],architecture=e.cr.check_architecture(model,2))
    for role,source in [('target',HERE/'code_retention_train.json'),('transfer',ROOT/'supervised014/transfer.json'),('controls',ROOT/'review013/controls.json')]:
        path=HERE/(role+'_candidate.json');rows=json.loads(source.read_text())
        report=json.loads(path.read_text()) if path.exists() else {'role':role,'metadata':meta,'rows':[],'protocol':{'greedy':True,'seed':0,'thinking':False,'cpu_threads':4,'code_max_new_tokens':320,'control_max_new_tokens':64,'solutions_in_generation_input':False,'tests_in_generation_input':False,'historical_diagnostic_not_fresh':True}}
        assert report['metadata']['checkpoint_stream_sha256']==m['stream_sha256']
        if report.get('status')=='complete':continue
        seen={r['id'] for r in report['rows']}
        for row in rows:
            if row['id'] in seen:continue
            question=row['question'] if role=='controls' else row['prompt']
            out=e.cr.generate(model,tok,question,max_tokens=cfg['control_max_new_tokens'] if role=='controls' else cfg['code_max_new_tokens']);out.pop('trace',None)
            score={'correct':e.cr.grade(out['output'],row)[0]} if role=='controls' else judge(out['output'],row)
            report['rows'].append({'id':row['id'],**out,**score});e.cr.atomic_json(path,report)
            save('status.json',{'status':'screen_'+role,'model_process_active':True,'completed_in_phase':len(report['rows']),'checkpoint_promoted':False,'process_continues_in_background':False})
            print('SCREEN',role,row['id'],score.get('all_passed',score.get('correct')),round(out['seconds'],2),flush=True)
        if role=='controls':report.update(correct=sum(r['correct'] for r in report['rows']),anchor_nll=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True))
        else:report.update(tasks_passed=sum(r['all_passed'] for r in report['rows']),test_groups_passed=sum(r['passed'] for r in report['rows']),test_groups_total=sum(r['total'] for r in report['rows']))
        report.update(total=len(rows),status='complete');e.cr.atomic_json(path,report)
    save('status.json',{'status':'screen_complete_pending_gate','model_process_active':False,'checkpoint_promoted':False,'process_continues_in_background':False})
if __name__=='__main__':main()
