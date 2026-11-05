"""Deterministic bounded activation intervention, never a saved weight edit."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'diagnostic011'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,e,torch,tasks,PARENT_HASH
from native010.native_runtime import tensor_hash

@torch.inference_mode()
def main():
 f=json.loads((HERE/'gate_probe_frozen.json').read_text())
 for path,digest in f['files'].items():assert e.cr.file_hash(ROOT/path)==digest,path
 p=HERE/'gate_probe.json';assert not p.exists(),'Do not repeat a completed sensitivity probe'
 status=json.loads((HERE/'status.json').read_text());status.update(status='gate_sensitivity',model_process_active=True);e.cr.atomic_json(HERE/'status.json',status)
 model,tok,parent,meta=load();before={n:tensor_hash(p) for n,p in model.named_parameters()}
 report={'status':'running','layers':f['layers'],'rows':[],'parent_sha256':PARENT_HASH,'weights_changed':False,'local_sensitivity_only':True,'gold_or_correct_target_in_context':False}
 for task in tasks(f['error_ids']):
  data=torch.load(HERE/'activations'/f"{task['id']}.pt",weights_only=True)
  step=data['suspected_point']['actual_token_index'];assert step is not None
  own=data['own_generated_token_ids'];prompt=e.cr.prompt(tok,task['prompt']);context=torch.cat([prompt,own[:step].view(1,-1)],-1)
  original_token=int(own[step]);baseline=model(input_ids=context,use_cache=False,logits_to_keep=1).logits[0,-1].float()
  base_top=int(baseline.argmax());base_lp=float(baseline[original_token]-baseline.logsumexp(0))
  row={'id':task['id'],'own_prefix_tokens':step,'suspected_span':data['suspected_point']['marker'],'original_token_id':original_token,
    'full_prefill_baseline_top_id':base_top,'cached_generation_token_matches_full_prefill':base_top==original_token,
    'baseline_logprob_original_token':base_lp,'probes':[]}
  for layer in f['layers']:
   module=model.model.language_model.layers[layer].linear_attn.in_proj_a
   for dose in [.99,1.01]:
    changes=[]
    def hook(module,args,output):
     altered=output.clone();altered[:,-1]=(output[:,-1].float()*dose).to(output.dtype)
     changes.append(float((altered[:,-1].float()-output[:,-1].float()).norm()/output[:,-1].float().norm().clamp_min(1e-12)))
     return altered
    handle=module.register_forward_hook(hook)
    try:logits=model(input_ids=context,use_cache=False,logits_to_keep=1).logits[0,-1].float()
    finally:handle.remove()
    delta=logits-baseline
    row['probes'].append({'layer':layer,'requested_activation_scale':dose,'actual_relative_change_by_visit':changes,
      'max_abs_logit_change':float(delta.abs().max()),'l2_logit_change':float(delta.norm()),'argmax_changed':int(logits.argmax())!=base_top,
      'new_top_id':int(logits.argmax()),'delta_logprob_own_original_token':float(logits[original_token]-logits.logsumexp(0))-base_lp})
  report['rows'].append(row);e.cr.atomic_json(p,report);print('GATE_SENSITIVITY',task['id'],sum(x['argmax_changed'] for x in row['probes']),flush=True)
 after={n:tensor_hash(p) for n,p in model.named_parameters()};assert before==after
 report.update(status='complete',all_parameter_hashes_unchanged=True,correctness_gain_evaluated=False,checkpoint_promoted=False)
 e.cr.atomic_json(p,report);status.update(status='gate_sensitivity_complete',model_process_active=False);e.cr.atomic_json(HERE/'status.json',status)
if __name__=='__main__':main()
