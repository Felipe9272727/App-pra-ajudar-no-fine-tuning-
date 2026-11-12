"""Small supervised joint Loop/mHC/temporal pilot, exact general parent preserved."""
import gc,json,math,sys,time,hashlib,io,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reasoning018'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
from train_runtime import torch,e,materialize,CheckpointVisits,loss,project_gains,tensor_hash
PARENT=tr.PARENT_HASH

def save(name,data):e.cr.atomic_json(HERE/name,data)
def mem():
 s=Path('/proc/self/status').read_text();return {k:int(s.split(label+':')[1].split()[0]) for k,label in [('rss_kb','VmRSS'),('peak_rss_kb','VmHWM')]}
def verify():
 for p,h in json.loads((HERE/'frozen.json').read_text()).items():assert tr.sha(ROOT/p)==h,p

def encode(tok,row):
 prefix=e.cr.prompt(tok,row['prompt'],thinking=True)
 targets=tok.encode(row['reasoning_explanation']+'\n</think>\n\n'+row['solution'],add_special_tokens=False)+[248044]
 ids=torch.cat([prefix,torch.tensor([targets])],1)
 assert ids.shape[1]<384 and 248046 not in targets
 return ids[:,:-1],torch.tensor(targets)

def family(n):
 if '.mhc_' in n:return 'mhc'
 if 'native_visit_gain' in n:return 'loop_gain'
 if any(x in n for x in ['.in_proj_a.','.in_proj_b.','.conv1d.','.A_log','.dt_bias']):return 'temporal'
 return 'normalization'

@torch.no_grad()
def trust(eligible,baseline,cfg):
 excess=[]
 for n,p in eligible.items():
  ref=baseline[n];delta=p.float()-ref;limit=cfg['trust_relative']*max(float(ref.norm()),math.sqrt(p.numel())*cfg['trust_rms_floor']);length=float(delta.norm())
  if length>limit:p.copy_((ref+delta*(limit/length)).to(p.dtype))
 # Projection preserves the saved architectural invariant, report its rounding.
 for n,p in eligible.items():
  if 'native_visit_gain' in n:p.clamp_(min=1e-4);p.div_(p.sum())
 for n,p in eligible.items():
  ref=baseline[n];ratio=float((p.float()-ref).norm())/max(float(ref.norm()),math.sqrt(p.numel())*cfg['trust_rms_floor'])
  if ratio>cfg['trust_relative']*1.001:excess.append({'name':n,'relative_l2':ratio})
 return excess

def main():
 verify();assert not (HERE/'steps.jsonl').exists(),'Investigate prior state; do not restart blindly'
 cfg=json.loads((HERE/'config.json').read_text());sel=json.loads((HERE/'trainable.json').read_text());code=json.loads((HERE/'code_train.json').read_text());general=json.loads((HERE/'general_train.json').read_text());started=time.monotonic();torch.manual_seed(cfg['seed'])
 model,tok,parent,meta=tr.load();del parent;materialize(model);before={n:tensor_hash(p) for n,p in model.named_parameters()};assert len(before)==699
 model.train();model.model.visual.eval();torch.set_grad_enabled(True)
 for n,p in model.named_parameters():p.requires_grad_(n in sel['names'])
 eligible={n:p for n,p in model.named_parameters() if p.requires_grad};assert set(eligible)==set(sel['names']) and sum(p.numel() for p in eligible.values())==2675888
 baseline={n:p.detach().float().clone() for n,p in eligible.items()};wrapper=CheckpointVisits(model)
 # Ordinary accumulation is inexpensive for2.7M selected values; backward each
 # example separately to avoid retaining two long activation graphs in8GiB.
 optimizer=torch.optim.Adafactor(list(eligible.values()),lr=cfg['learning_rate'],eps=(1e-16,1e-3),beta2_decay=-.8,d=1.,weight_decay=0.,foreach=False)
 ids,gold=encode(tok,code[0]);value=loss(model,ids,gold);value.backward()
 assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in eligible.values())
 assert all(wrapper.calls[(i,v)]>=2 for i in range(4,28) for v in (0,1))
 assert all(tensor_hash(dict(model.named_parameters())[n])==h for n,h in before.items())
 save('backward_preflight.json',{'all_699_hashes_unchanged':True,'selected_tensors':len(eligible),'gradient_present':sum(p.grad is not None for p in eligible.values()),'nonzero_gradients':sum(bool(p.grad.count_nonzero()) for p in eligible.values()),'both_visits_in_forward_and_backward_recompute':True,'loss':float(value.detach()),'sequence_tokens':ids.shape[1],**mem()})
 optimizer.zero_grad(set_to_none=True);del ids,gold,value;gc.collect();ever=set();all_excess=[]
 for step,(c,g) in enumerate(zip(code,general),1):
  optimizer.zero_grad(set_to_none=True);values=[]
  for row in (c,g):
   ids,gold=encode(tok,row);value=loss(model,ids,gold);values.append(float(value.detach()));(value*.5).backward();del ids,gold,value
  assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in eligible.values())
  nonzero={n for n,p in eligible.items() if bool(p.grad.count_nonzero())};ever.update(nonzero);optimizer.step();excess=trust(eligible,baseline,cfg);all_excess.append({'step':step,'rows':excess})
  entry={'step':step,'examples':[c['id'],g['id']],'code_nll_before_update':values[0],'general_nll_before_update':values[1],'nonzero_gradient_tensors':len(nonzero),'nonzero_by_family':{f:sum(family(n)==f for n in nonzero) for f in ['mhc','loop_gain','temporal','normalization']},'post_projection_cap_excess_count':len(excess),**mem()}
  with (HERE/'steps.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
  save('status.json',{'status':'training','optimizer_steps_completed':step,'model_process_active':True,'checkpoint_promoted':False,'process_continues_in_background':False});print('TRAIN018',json.dumps(entry),flush=True);gc.collect()
 after={n:tensor_hash(p) for n,p in model.named_parameters()};assert all(after[n]==h for n,h in before.items() if n not in eligible)
 ck=HERE/'checkpoints';ck.mkdir(exist_ok=True)
 payload={'format':'selected-parameters-v1','parent_sha256':PARENT,'parameters':{n:p.detach().cpu().clone() for n,p in eligible.items()}}
 buffer=io.BytesIO();torch.save(payload,buffer);raw=buffer.getvalue();compressed=gzip.compress(raw,compresslevel=6,mtime=0);(ck/'candidate.pt.gz').write_bytes(compressed)
 torch.save({'optimizer':optimizer.state_dict(),'steps':8,'rng':torch.get_rng_state()},ck/'optimizer.pt')
 changes={n:{'shape':list(p.shape),'dtype':str(p.dtype),'before_sha256':before[n],'after_sha256':after[n],'changed_values':int((p.detach().view(torch.int16 if p.element_size()==2 else torch.int32)!=baseline[n].to(p.dtype).view(torch.int16 if p.element_size()==2 else torch.int32)).count_nonzero()),'family':family(n)} for n,p in eligible.items()}
 audit={'status':'training_complete_pending_cold_restore','parent_sha256':PARENT,'optimizer_steps':8,'eligible_tensors':329,'eligible_parameters':2675888,'ever_nonzero_gradients':sorted(ever),'changed_tensors':sum(v['changed_values']>0 for v in changes.values()),'changed_values':sum(v['changed_values'] for v in changes.values()),'frozen_370_parameter_tensors_unchanged':True,'vision_153_unchanged':True,'all_699_finite':all(bool(torch.isfinite(p).all()) for p in model.parameters()),'parameters':changes,'all_699_before':before,'all_699_after':after,'checkpoint_sha256':hashlib.sha256(compressed).hexdigest(),'checkpoint_raw_sha256':hashlib.sha256(raw).hexdigest(),'compressed_bytes':len(compressed),'both_loop_visits_jointly_trained':True,'post_projection_trust_cap_excess':all_excess,'seconds':time.monotonic()-started,**mem()}
 model.requires_grad_(False);audit['architecture']=e.cr.check_architecture(model,2);audit['architecture'].update(optimizer_updates=8,backward_passes=17,preflight_backward_passes=1,training_example_backward_passes=16);audit['visit_recompute_calls']={str(k):v for k,v in wrapper.calls.items()};audit['loop_gains_before_after']={n:{'before':baseline[n].tolist(),'after':p.detach().tolist()} for n,p in eligible.items() if 'native_visit_gain' in n};save('training_complete.json',audit);wrapper.close();del wrapper,optimizer,eligible,model,baseline,payload,buffer,raw,compressed;gc.collect();torch.set_grad_enabled(False)
 # Cold loader, single model resident, exact per-parameter reconstruction.
 from reasoning018.restore import load_candidate
 restored,_,_,_=load_candidate();assert all(tensor_hash(dict(restored.named_parameters())[n])==h for n,h in after.items());del restored;gc.collect()
 audit.update(status='training_complete_cold_restore_verified',cold_restore_all_699_hashes_verified=True);save('training_complete.json',audit);save('status.json',{'status':'trained_pending_retention_gate','model_process_active':False,'checkpoint_promoted':False,'process_continues_in_background':False});print('TRAIN018_COMPLETE',audit['changed_tensors'],audit['changed_values'],flush=True)
if __name__=='__main__':main()
