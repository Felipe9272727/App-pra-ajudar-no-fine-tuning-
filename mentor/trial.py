"""One assistant-selected direct-weight trial; pause for review after results."""
import copy,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'mentor'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'rsi100'))
os.environ.setdefault('LS_CPU_THREADS','4')
import engine as e
from local_cpu.sandbox import evaluate
from policy import accept_paired,dominates,flatten
from checkpoint_io import tensor_checkpoint
import torch
e.cr.evaluate=evaluate
runtime_provenance=e.provenance
def provenance():
    result=runtime_provenance();result['source_commit']=os.environ.get('MENTOR_SOURCE_COMMIT')
    result['execution']='local CPU with canonical AST judge under seccomp'
    result['protocol']['executor']='capability-cleared syscall-filtered subprocess'
    for p in [HERE/'trial.py',HERE/'diagnose.py',ROOT/'local_cpu/sandbox.py']:
        result['code_sha256'][str(p.relative_to(ROOT))]=e.cr.file_hash(p)
    return result
e.provenance=provenance

def save(report,stage):
    report['stage']=stage;report['updated_unix']=time.time()
    e.cr.atomic_json(HERE/'trial_001.json',report)
    e.cr.atomic_json(HERE/'status.json',{'status':stage,'trial':1,'controller':'assistant',
      'legacy_rounds_completed':31,'legacy_search_paused':True,'checkpoint_promoted':False,
      'model_process_active':stage not in ['rejected_on_screen','rejected_full_evaluation','eligible_for_fresh_validation'],
      'backward_passes':0,'final_test_evaluated':False,'updated_unix':time.time()})
    print('MENTOR_STAGE',stage,flush=True)

@torch.inference_mode()
def main():
    model,_=e.cr.load('baseline');tok=e.cr.tokenizer();parent=e.read_checkpoint('best.pt')
    directions=torch.load(HERE/'directions_001.pt',weights_only=True)
    assert directions['parent_checkpoint_sha256']==e.cr.file_hash(e.CK/'best.pt')
    historical=json.loads((e.HERE/'best_metrics.json').read_text())
    task=next(t for t in e.DATA['search']+e.DATA['guard'] if t['id']=='overlap_count')
    report={'trial':1,'hypothesis_file':'mentor/hypothesis_001.json','source_commit':os.environ.get('MENTOR_SOURCE_COMMIT'),
      'parent_checkpoint_sha256':e.cr.file_hash(e.CK/'best.pt'),'direction_sha256':e.cr.file_hash(HERE/'directions_001.pt'),
      'fraction':.003,'edited_parameter':'model.language_model.layers.31.mlp.down_proj.weight',
      'reference_or_correct_next_token_supplied':False,'backward_passes':0,
      'heldout_used':False,'checkpoint_promoted':False,'quality_claim':'none until full paired and historical tests plus fresh validation'}
    save(report,'measuring_parent_screen');e.apply(model,parent)
    base=e.coding(model,tok,[task]);report['parent_screen']=base
    norm=parent['dense_weight'].float().norm()
    variants={}
    for name,key in [('matched_random','random_output_direction'),('negative','bad_output_direction')]:
        proposal=copy.deepcopy(parent)
        proposal['dense_weight']=(parent['dense_weight'].float()-.003*norm*torch.outer(directions[key],directions['input_direction'])).to(parent['dense_weight'].dtype)
        arch=e.apply(model,proposal)
        result=e.coding(model,tok,[task]);report[name+'_screen']=result
        report[name+'_edit']={'actual_relative_norm':float((proposal['dense_weight'].float()-parent['dense_weight'].float()).norm()/norm),
          'changed_values':int((proposal['dense_weight']!=parent['dense_weight']).sum()),'architecture':arch}
        save(report,'screened_'+name)
        if name=='negative':candidate=proposal
    if not dominates(flatten(report['negative_screen']),flatten(base)):
        report['accepted_for_validation']=False;report['reason']='No strict gain without case regression on the observed screen'
        e.apply(model,parent);save(report,'rejected_on_screen');return
    e.apply(model,parent);save(report,'measuring_full_paired_parent')
    paired=e.full_score(model,tok);report['paired_parent']=paired
    e.apply(model,candidate);save(report,'measuring_full_candidate')
    measured=e.full_score(model,tok);report['full_candidate']=measured
    accepted,reason=accept_paired(measured,paired,historical)
    report.update(accepted_for_validation=accepted,reason=reason)
    if accepted:
        candidate['mentor_trial']=1
        tensor_checkpoint(candidate,HERE/'checkpoints/negative_001.pt')
        report['candidate_checkpoint_sha256']=e.cr.file_hash(HERE/'checkpoints/negative_001.pt')
    e.apply(model,parent)
    save(report,'eligible_for_fresh_validation' if accepted else 'rejected_full_evaluation')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        e.cr.atomic_json(HERE/'status.json',{'status':'interrupted','trial':1,'model_process_active':False,
          'checkpoint_promoted':False,'backward_passes':0,'error':str(exc),'updated_unix':time.time()})
        raise
