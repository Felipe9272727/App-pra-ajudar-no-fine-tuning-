"""Recover the already-saved eight-update checkpoint; NEVER perform training."""
import json,gzip,hashlib,io,sys,gc,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reasoning018';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
@tr.torch.inference_mode()
def main():
 recovery=json.loads((HERE/'recovery.json').read_text());assert recovery['updates_saved']==8
 old=json.loads((HERE/'frozen_initial.json').read_text())
 for p,h in old.items():assert tr.sha(HERE/'train_initial.py' if p=='reasoning018/train.py' else ROOT/p)==h,p
 assert not (HERE/'training_complete.json').exists()
 data=(HERE/'checkpoints/candidate.pt.gz').read_bytes();assert hashlib.sha256(data).hexdigest()==recovery['checkpoint_sha256'];raw=gzip.decompress(data);payload=tr.torch.load(io.BytesIO(raw),weights_only=True);assert payload['parent_sha256']==tr.PARENT_HASH
 state=tr.torch.load(HERE/'checkpoints/optimizer.pt',weights_only=True);assert state['steps']==8;assert set(int(s['step']) for s in state['optimizer']['state'].values())=={8};assert len(state['optimizer']['state'])==329
 model,tok,parent,meta=tr.load();del parent
 before={n:tr.tensor_hash(p) for n,p in model.named_parameters()};params=dict(model.named_parameters());changes={};gains={};excess=[]
 for n,value in payload['parameters'].items():
  p=params[n];assert p.dtype==value.dtype and p.shape==value.shape;oldp=p.detach().float();itype=tr.torch.int16 if p.element_size()==2 else tr.torch.int32;count=int((p.detach().view(itype)!=value.view(itype)).count_nonzero());limit=.002*max(float(oldp.norm()),math.sqrt(p.numel())*.001);distance=float((value.float()-oldp).norm());family='mhc' if '.mhc_' in n else 'loop_gain' if 'native_visit_gain' in n else 'temporal' if any(s in n for s in ['.in_proj_a.','.in_proj_b.','.conv1d.','.A_log','.dt_bias']) else 'normalization'
  changes[n]={'shape':list(p.shape),'dtype':str(p.dtype),'before_sha256':before[n],'after_sha256':tr.tensor_hash(value),'changed_values':count,'family':family,'final_relative_l2':distance/max(float(oldp.norm()),math.sqrt(p.numel())*.001)}
  if distance>limit*1.001:excess.append({'name':n,'relative_l2':changes[n]['final_relative_l2']})
  if 'native_visit_gain' in n:gains[n]={'before':p.tolist(),'after':value.tolist()}
  p.copy_(value)
 after={n:tr.tensor_hash(p) for n,p in model.named_parameters()};assert len(before)==len(after)==699;assert all(after[n]==h for n,h in before.items() if n not in payload['parameters']);assert all(bool(tr.torch.isfinite(p).all()) for p in model.parameters())
 steps=[json.loads(s) for s in (HERE/'steps.jsonl').read_text().splitlines()];assert [s['step'] for s in steps]==list(range(1,9))
 architecture=tr.e.cr.check_architecture(model,2);architecture.update(optimizer_updates=8,backward_passes=17,preflight_backward_passes=1,training_example_backward_passes=16,provenance='Eight persisted step records, optimizer step8 for329leaves, and immutable training source; visit-correct backward preflight persisted. Runtime checker zero placeholder is not training provenance.')
 audit={'status':'recovered_saved_checkpoint_pending_cold_restore','parent_sha256':tr.PARENT_HASH,'optimizer_steps':8,'eligible_tensors':329,'eligible_parameters':2675888,'nonzero_gradient_tensors_each_step':[s['nonzero_gradient_tensors'] for s in steps],'exact_nonzero_gradient_name_union':'not retained before audit assertion; do not invent','changed_tensors':sum(v['changed_values']>0 for v in changes.values()),'changed_values':sum(v['changed_values'] for v in changes.values()),'frozen_370_parameter_tensors_unchanged':True,'vision_153_unchanged':True,'all_699_finite':True,'parameters':changes,'all_699_before':before,'all_699_after':after,'checkpoint_sha256':recovery['checkpoint_sha256'],'checkpoint_raw_sha256':hashlib.sha256(raw).hexdigest(),'compressed_bytes':len(data),'both_loop_visits_jointly_trained':True,'per_step_post_projection_cap_excess_counts':[s['post_projection_cap_excess_count'] for s in steps],'final_post_projection_cap_excess':excess,'architecture':architecture,'loop_gains_before_after':gains,'audit_recovery':'No updates repeated; source checker ordering corrected only. Training timing/call-name union were not persisted before the exception.','training_peak_rss_kb':max(s['peak_rss_kb'] for s in steps)}
 tr.e.cr.atomic_json(HERE/'training_complete.json',audit)
 del state,model,params,payload,tok,value,p;gc.collect()
 from reasoning018.restore import load_candidate
 model,tok,meta,saved=load_candidate();assert all(tr.tensor_hash(p)==after[n] for n,p in model.named_parameters());del model;gc.collect()
 audit.update(status='training_complete_cold_restore_verified',cold_restore_all_699_hashes_verified=True);tr.e.cr.atomic_json(HERE/'training_complete.json',audit);recovery.update(status='checkpoint_recovered_no_training_repeated',all_699_cold_restore_verified=True);tr.e.cr.atomic_json(HERE/'recovery.json',recovery);tr.e.cr.atomic_json(HERE/'status.json',{'status':'trained_pending_retention_gate','model_process_active':False,'checkpoint_promoted':False,'optimizer_steps_completed':8,'process_continues_in_background':False});print('RECOVERED018',audit['changed_tensors'],audit['changed_values'],flush=True)
if __name__=='__main__':main()
