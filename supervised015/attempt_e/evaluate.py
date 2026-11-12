import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
"""Evaluate only the restored full-text specialist; reuse immutable old baselines."""
import json,time
import train_runtime
from train_runtime import *
HERE=ROOT/"supervised015/attempt_e"
train_runtime.HERE=HERE
import checkpoint as exact_checkpoint
from restore import load_d
from supervised014.judge import evaluate as judge

@torch.inference_mode()
def main():
    for path,h in json.loads((HERE/'evaluation_frozen.json').read_text()).items():assert sha(ROOT/path)==h,path
    training=json.loads((HERE/'training_complete.json').read_text())
    manifest=HERE/'checkpoints/candidate/manifest.json';assert manifest.exists()
    model,tok,meta,restored=load_d()
    meta.update(checkpoint_stream_sha256=restored['stream_sha256'],checkpoint_manifest_sha256=sha(manifest),
                architecture=e.cr.check_architecture(model,2),variant='full_text_supervised_specialist_015_attempt_e',
                training_backward_passes=training['new_total_gradient_updates_in_lineage'])
    meta['architecture']['backward_passes']=training['new_total_gradient_updates_in_lineage']
    meta['architecture']['limitations']='Qwen widths; Loop/mHC and Liquid-inspired operators, not full SenseNova/LFM3; trained text weights do not imply quality or faithful reasoning.'
    for role in ['target','transfer','controls']:
        path=HERE/(role+'_specialist.json')
        report=json.loads(path.read_text()) if path.exists() else {'role':role,'metadata':meta,'rows':[],
            'target_is_trained_on':True,'transfer_previously_observed_in_study014':True,'transfer_previously_observed_in_study015b':True,
            'protocol':{'max_new_tokens':320,'seed':0,'greedy':True,'thinking':False,'cpu_threads':4,
                        'reference_implementation_in_generation_prompt':False,'private_tests_in_generation_prompt':False}}
        assert report['metadata']['checkpoint_stream_sha256']==restored['stream_sha256']
        if report.get('status')=='complete':continue
        rows=json.loads((HERE/'train.json').read_text()) if role=='target' else json.loads((ROOT/('supervised014/transfer.json' if role=='transfer' else 'review013/controls.json')).read_text())
        seen={r['id'] for r in report['rows']}
        for row in rows:
            if row['id'] in seen:continue
            question=row['question'] if role=='controls' else row['prompt']
            out=e.cr.generate(model,tok,question,max_tokens=64 if role=='controls' else 320);out.pop('trace',None)
            if role=='controls':score={'correct':e.cr.grade(out['output'],row)[0]}
            else:score=judge(out['output'],row)
            report['rows'].append({'id':row['id'],**out,**score});e.cr.atomic_json(path,report)
            save('status.json',{'status':'evaluating_'+role,'model_process_active':True,'completed_in_phase':len(report['rows']),
                  'checkpoint_promoted':False,'parent_sha256':PARENT_HASH,'process_continues_in_background':False,'updated_unix':time.time()})
            print('EVAL',role,row['id'],score.get('all_passed',score.get('correct')),round(out['seconds'],2),flush=True)
        if role=='controls':
            report['correct']=sum(r['correct'] for r in report['rows'])
            report['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)
        else:
            report['tasks_passed']=sum(r['all_passed'] for r in report['rows'])
            report['test_groups_passed']=sum(r['passed'] for r in report['rows'])
            report['test_groups_total']=sum(r['total'] for r in report['rows'])
        report['total']=len(rows);report['status']='complete';e.cr.atomic_json(path,report)
    # Already-known counterexample is diagnostic, never part of official totals.
    row=next(r for r in json.loads((ROOT/'supervised014/transfer.json').read_text()) if r['id']=='MBPP/129')
    out=next(r for r in json.loads((HERE/'transfer_specialist.json').read_text())['rows'] if r['id']=='MBPP/129')
    row={**row,'tests':['assert magic_square_test([[8,1,6],[3,5,9],[4,7,2]]) == False']}
    save('known_counterexample.json',{'previously_observed':True,'included_in_official_score':False,**judge(out['output'],row)})
    save('status.json',{'status':'evaluation_complete_pending_report','model_process_active':False,'checkpoint_promoted':False,
             'parent_sha256':PARENT_HASH,'process_continues_in_background':False,'updated_unix':time.time()})

if __name__=='__main__':main()
