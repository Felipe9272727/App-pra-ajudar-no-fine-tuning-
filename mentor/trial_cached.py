"""Hypothesis 002: edit the actual cached decoding state, preserve prior tokens.

Choose dose by a predeclared negative-only token rule, then test fresh code.
No correct replacement token or reference solution enters generation.
"""
import copy,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'mentor'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'rsi100'))
os.environ.setdefault('LS_CPU_THREADS','4')
import engine as e
import torch
from mentor.diagnose import token_stats,capture
from local_cpu.sandbox import evaluate
from policy import accept_paired,dominates,flatten
from checkpoint_io import tensor_checkpoint
e.cr.evaluate=evaluate
original_provenance=e.provenance
def provenance():
    p=original_provenance();p['source_commit']=os.environ.get('MENTOR_SOURCE_COMMIT')
    p['execution']='local CPU, seccomp AST judge, external phase watchdog'
    for f in [HERE/'trial_cached.py',ROOT/'local_cpu/sandbox.py']:
        p['code_sha256'][str(f.relative_to(ROOT))]=e.cr.file_hash(f)
    return p
e.provenance=provenance

def save(report,stage):
    report.update(stage=stage,updated_unix=time.time())
    e.cr.atomic_json(HERE/'trial_002.json',report)
    e.cr.atomic_json(HERE/'status.json',{'status':stage,'trial':2,'controller':'assistant',
      'legacy_search_paused':True,'legacy_rounds_completed':31,'guided_trials_completed':1,
      'model_process_active':stage not in ['rejected_on_screen','rejected_full_evaluation','eligible_for_fresh_validation','no_token_effect_within_budget'],
      'checkpoint_promoted':False,'backward_passes':0,'final_test_evaluated':False,'updated_unix':time.time()})
    print('MENTOR_002',stage,flush=True)

@torch.inference_mode()
def cached_logits(model,prompt,prefix):
    # Use the identical GenerationMixin preparation/cache/position path. Force
    # only the student's already-generated prefix; the target remains free.
    length=prompt.shape[1];all_ids=list(range(model.get_output_embeddings().weight.shape[0]))
    def allowed(batch_id,current):
        step=current.shape[0]-length
        return [prefix[step]] if step<len(prefix) else all_ids
    result=e.call('mentor002_same_generation_path',model.generate,input_ids=prompt,
      max_new_tokens=len(prefix)+1,use_cache=True,do_sample=False,pad_token_id=model.config.text_config.eos_token_id,
      return_dict_in_generate=True,output_scores=True,prefix_allowed_tokens_fn=allowed)
    return result.scores[-1][0].float()

@torch.inference_mode()
def main():
    model,_=e.call('mentor002_load',e.cr.load,'baseline',budget=300);tok=e.cr.tokenizer()
    parent=e.read_checkpoint('best.pt');e.apply(model,parent)
    task=next(t for t in e.DATA['search']+e.DATA['guard'] if t['id']=='overlap_count')
    prompt=e.cr.prompt(tok,task['prompt']);states=[]
    hook=model.model.language_model.layers[31].mlp.down_proj.register_forward_pre_hook(lambda module,inputs:states.append(inputs[0][0,-1].detach().float().clone()))
    try:
        torch.manual_seed(0)
        generation=e.call('mentor002_parent_generation',model.generate,input_ids=prompt,max_new_tokens=160,use_cache=True,do_sample=False,
          pad_token_id=tok.eos_token_id,return_dict_in_generate=True,output_scores=True)
    finally:hook.remove()
    ids=generation.sequences[0,prompt.shape[1]:].tolist();text=tok.decode(ids,skip_special_tokens=True)
    assert len(states)==len(generation.scores)==len(ids)
    marker='i += len(sub)';assert marker in text,'Inspect new response before selecting a target'
    char=text.index('len',text.index(marker));bounds=[len(tok.decode(ids[:i],skip_special_tokens=True)) for i in range(len(ids)+1)]
    target=next(i for i in range(len(ids)) if bounds[i]<=char<bounds[i+1]);bad=ids[target]
    assert 'len' in tok.decode([bad])
    h=states[target];preserve=torch.stack(states[:target]);ridge=1e-5*float(preserve.square().sum(1).mean())
    direction=h-preserve.T@torch.linalg.solve(preserve@preserve.T+ridge*torch.eye(len(preserve)),preserve@h)
    assert float(direction.norm())>1e-6
    direction/=direction.norm()
    output=model.get_output_embeddings().weight[bad].detach().float().clone();output/=output.norm()
    report={'trial':2,'source_commit':os.environ.get('MENTOR_SOURCE_COMMIT'),'hypothesis_file':'mentor/hypothesis_002.json',
      'parent_checkpoint_sha256':e.cr.file_hash(e.CK/'best.pt'),'backward_passes':0,'heldout_used':False,
      'checkpoint_promoted':False,'correct_replacement_token_or_solution_supplied':False,
      'parent_output':text,'parent_token_ids':ids,'target_index':target,'bad_token_id':bad,'bad_piece':tok.decode([bad]),
      'preserved_prior_token_count':target,'preservation_projection_ratios':(preserve@direction/preserve.norm(dim=1)).tolist(),
      'generation_before':token_stats(generation.scores[target][0].float(),bad,tok),'dose_probes':[]}
    save(report,'captured_actual_decoding_activations')
    initial=cached_logits(model,prompt,ids[:target]);report['exact_cached_before']=token_stats(initial,bad,tok)
    replay_error=abs(report['exact_cached_before']['bad_token_log_odds']-report['generation_before']['bad_token_log_odds'])
    report['cached_replay_log_odds_error']=replay_error
    save(report,'checked_same_generation_replay')
    assert report['exact_cached_before']['top'][0]['id']==bad and replay_error<.5,'Cached replay diverged; inspect before editing'
    old=torch.load(HERE/'directions_001.pt',weights_only=True);norm=parent['dense_weight'].float().norm()
    old_proposal=copy.deepcopy(parent)
    old_proposal['dense_weight']=(parent['dense_weight'].float()-.003*norm*torch.outer(old['bad_output_direction'],old['input_direction'])).to(parent['dense_weight'].dtype)
    e.apply(model,old_proposal);report['previous_edit_exact_cached']=token_stats(cached_logits(model,prompt,ids[:target]),bad,tok)
    candidate=None
    for fraction in [.003,.006,.012,.02]:
        proposal=copy.deepcopy(parent)
        proposal['dense_weight']=(parent['dense_weight'].float()-fraction*norm*torch.outer(output,direction)).to(parent['dense_weight'].dtype)
        e.apply(model,proposal);stats=token_stats(cached_logits(model,prompt,ids[:target]),bad,tok)
        report['dose_probes'].append({'fraction':fraction,'actual_relative_norm':float((proposal['dense_weight'].float()-parent['dense_weight'].float()).norm()/norm),
          'changed_values':int((proposal['dense_weight']!=parent['dense_weight']).sum()),'cached_score':stats})
        save(report,'probing_cached_dose')
        if stats['top'][0]['id']!=bad:
            candidate=proposal;report['chosen_fraction']=fraction;break
    e.apply(model,parent)
    if candidate is None:
        save(report,'no_token_effect_within_budget');return
    e.apply(model,parent);base=e.coding(model,tok,[task]);report['parent_screen']=base
    random=copy.deepcopy(parent)
    random['dense_weight']=(parent['dense_weight'].float()-report['chosen_fraction']*norm*torch.outer(old['random_output_direction'],direction)).to(parent['dense_weight'].dtype)
    e.apply(model,random);report['matched_random_screen']=e.coding(model,tok,[task])
    e.apply(model,candidate);screen=e.coding(model,tok,[task]);report['candidate_screen']=screen
    if not dominates(flatten(screen),flatten(base)):
        report['accepted_for_validation']=False;report['reason']='No strict screening gain without case loss'
        e.apply(model,parent);save(report,'rejected_on_screen');return
    save(report,'screen_passed_measuring_full_parent');e.apply(model,parent)
    paired=e.full_score(model,tok);report['full_paired_parent']=paired
    save(report,'measuring_full_candidate');e.apply(model,candidate)
    measured=e.full_score(model,tok);report['full_candidate']=measured
    historical=json.loads((e.HERE/'best_metrics.json').read_text())
    accepted,reason=accept_paired(measured,paired,historical);report.update(accepted_for_validation=accepted,reason=reason)
    if accepted:
        candidate['mentor_trial']=2;tensor_checkpoint(candidate,HERE/'checkpoints/negative_002.pt')
        report['candidate_checkpoint_sha256']=e.cr.file_hash(HERE/'checkpoints/negative_002.pt')
    e.apply(model,parent);save(report,'eligible_for_fresh_validation' if accepted else 'rejected_full_evaluation')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        e.cr.atomic_json(HERE/'status.json',{'status':'interrupted','trial':2,'model_process_active':False,'checkpoint_promoted':False,'error':str(exc),'updated_unix':time.time()})
        raise
