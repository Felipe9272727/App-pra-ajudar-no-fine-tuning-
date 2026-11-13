"""Three real epochs on loop block + opened exits; parent and all epochs retained."""
import argparse,collections,gc,gzip,json,math,os,time
from pathlib import Path
from loop_runtime import *
from train_runtime import materialize,CheckpointVisits,loss,tensor_hash

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');a=ap.parse_args();verify();cfg=read('config.json');sel=read('trainable.json');code=read('code_train.json');general=read('general_train.json');torch.manual_seed(cfg['seed']);torch.set_num_threads(4);start=time.monotonic();rolling=Path('/dev/shm/liquid-loop025/latest.pt.gz.bin');journal=HERE/'steps.jsonl'
 assert a.resume or (not rolling.exists() and not journal.exists()),'Inspect previous state; use explicit recovery, never blind restart'
 model,tok,parent,meta=tr.load();del parent;torch.set_num_threads(4);materialize(model);before={n:tensor_hash(p) for n,p in model.named_parameters()};assert len(before)==699
 model.train();model.model.visual.eval();torch.set_grad_enabled(True)
 for n,p in model.named_parameters():p.requires_grad_(n in sel['names'])
 ps=dict(model.named_parameters());eligible={n:p for n,p in ps.items() if p.requires_grad};assert len(eligible)==292 and sum(p.numel() for p in eligible.values())==48340208
 exits=set(sel['exit_names']);assert all(not bool(eligible[n].count_nonzero()) for n in exits)
 baseline={n:p.detach().float().clone() for n,p in eligible.items()};wrapper=CheckpointVisits(model);fams={n:family(n) for n in eligible};optimizer=torch.optim.Adafactor([{'params':[p for n,p in eligible.items() if n not in exits],'lr':cfg['learning_rate_controllers']},{'params':[eligible[n] for n in eligible if n in exits],'lr':cfg['learning_rate_exits']}],eps=(1e-16,1e-3),beta2_decay=-.8,d=1.,weight_decay=0.,foreach=False);completed=0;ever=set();step_records=[]
 def teacher_probe():
  model.eval();vals=[]
  with torch.no_grad():
   for row in [code[0],general[0]]:
    ids,gold=encode(tok,row);vals.append({'id':row['id'],'nll':float(loss(model,ids,gold))})
  model.train();model.model.visual.eval();return vals
 if a.resume:
  latest=read('rolling.json');assert hashfile(rolling)==latest['sha256']
  with gzip.open(rolling,'rb') as z:state=torch.load(z,weights_only=True,map_location='cpu')
  assert state['parent_sha256']==tr.PARENT_HASH and state['before_hashes']==before
  with torch.no_grad():
   for n,p in state['parameters'].items():eligible[n].copy_(p)
  optimizer.load_state_dict(state['optimizer']);torch.set_rng_state(state['rng']);completed=state['step'];ever=set(state['ever_nonzero']);step_records=[json.loads(s) for s in journal.read_text().splitlines()] if journal.exists() else []
  if len(step_records)==completed-1:
   with journal.open('a') as f:f.write(json.dumps(state['last_entry'])+'\n')
   step_records.append(state['last_entry'])
  assert len(step_records)==completed;del state;gc.collect();print('RESUMED_EXACT_ROLLING_STEP',completed,flush=True)
 else:
  save('before.json',{'parent_sha256':tr.PARENT_HASH,'all_699_before':before,'selected':sel,'initial_teacher_probe':teacher_probe(),**memory()})
  ids,gold=encode(tok,code[0]);v=loss(model,ids,gold);v.backward();assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in eligible.values());assert all(wrapper.calls[(i,j)]>=2 for i in range(4,28) for j in (0,1));assert all(tensor_hash(p)==before[n] for n,p in ps.items())
  nz=sorted(n for n,p in eligible.items() if bool(p.grad.count_nonzero()));save('backward_preflight.json',{'status':'passed_no_weight_update','selected_tensors':len(eligible),'gradient_present':len(eligible),'nonzero_gradient_names':nz,'new_exit_gradients':sum(n in exits for n in nz),'both_visits_recomputed':True,'all699_unchanged':True,'loss':float(v.detach()),**memory()});optimizer.zero_grad(set_to_none=True);del ids,gold,v;gc.collect()
 def epoch_snapshot(epoch):
  after={n:tensor_hash(p) for n,p in ps.items()};assert all(after[n]==h for n,h in before.items() if n not in eligible);assert all(bool(torch.isfinite(p).all()) for p in ps.values());changes={n:{'family':fams[n],'changed_values':int((p.detach().float()!=baseline[n]).count_nonzero()),'before':before[n],'after':after[n]} for n,p in eligible.items()};audit={'epoch':epoch,'steps':epoch*8,'all_699_after':after,'selected_tensors':292,'selected_values':48340208,'changed_tensors':sum(v['changed_values']>0 for v in changes.values()),'changed_values':sum(v['changed_values'] for v in changes.values()),'changes':changes,'ever_nonzero_gradient_names':sorted(ever),'formerly_blocked_gradient_names_observed':[n for n in read('formerly_blocked.json') if n in ever],'frozen407_unchanged':True,'vision153_unchanged':True,'all_finite':True,'teacher_probe':teacher_probe(),'both_loop_visits_jointly_trained':True,'visit_recompute_calls':{str(k):v for k,v in wrapper.calls.items()},'seconds_descriptive':time.monotonic()-start,**memory()};m=export_epoch(rolling,epoch,audit);print('EPOCH_SAVED',epoch,m['compressed_bytes'],audit['changed_values'],flush=True)
 if completed and completed%8==0 and not (HERE/'checkpoints'/f'epoch{completed//8:02d}'/'manifest.json').exists():epoch_snapshot(completed//8)
 for epoch in range(1,cfg['epochs']+1):
  order=torch.randperm(8,generator=torch.Generator().manual_seed(cfg['seed']+epoch)).tolist()
  for position,index in enumerate(order):
   step=(epoch-1)*8+position+1
   if step<=completed:continue
   optimizer.zero_grad(set_to_none=True);values=[]
   for row in [code[index],general[index]]:
    ids,gold=encode(tok,row);v=loss(model,ids,gold);values.append(float(v.detach()));(v*.5).backward();del ids,gold,v
   assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in eligible.values());nz={n for n,p in eligible.items() if bool(p.grad.count_nonzero())};ever.update(nz);torch.nn.utils.clip_grad_norm_(list(eligible.values()),1.);optimizer.step();excess=[]
   with torch.no_grad():
    for n,p in eligible.items():
     ref=baseline[n];delta=p.float()-ref;den=max(float(ref.norm()),math.sqrt(p.numel())*cfg['trust_rms_floor']);cap=(cfg['trust_exits'] if n in exits else cfg['trust_controllers'])*den;length=float(delta.norm())
     if length>cap:p.copy_((ref+delta*(cap/length)).to(p.dtype))
    for n,p in eligible.items():
     if 'native_visit_gain' in n:p.clamp_(min=1e-4);p.div_(p.sum())
    for n,p in eligible.items():
     ref=baseline[n];ratio=float((p.float()-ref).norm())/max(float(ref.norm()),math.sqrt(p.numel())*cfg['trust_rms_floor']);cap=cfg['trust_exits'] if n in exits else cfg['trust_controllers']
     if ratio>cap*1.001:excess.append({'name':n,'relative_l2':ratio,'cap':cap})
   optimizer.zero_grad(set_to_none=True);entry={'step':step,'epoch':epoch,'pair_id':index,'examples':[code[index]['id'],general[index]['id']],'code_nll_before_update':values[0],'general_nll_before_update':values[1],'nonzero_gradient_names':sorted(nz),'nonzero_by_family':dict(collections.Counter(fams[n] for n in nz)),'post_BF16_projection_overshoots':excess,**memory()};state={'format':'loop025-training-state-v1','parent_sha256':tr.PARENT_HASH,'parameters':{n:p.detach() for n,p in eligible.items()},'optimizer':optimizer.state_dict(),'rng':torch.get_rng_state(),'step':step,'before_hashes':before,'ever_nonzero':sorted(ever),'last_entry':entry};tmp=rolling.with_suffix('.tmp')
   with gzip.open(tmp,'wb',compresslevel=1) as z:torch.save(state,z)
   tmp.replace(rolling);save('rolling.json',{'step':step,'sha256':hashfile(rolling),'path':str(rolling),'not_durable_until_epoch_parts_published':True});del state
   with journal.open('a') as f:f.write(json.dumps(entry)+'\n')
   step_records.append(entry);completed=step;save('status.json',{'status':'training','optimizer_steps':step,'epoch':epoch,'model_process_active':True,'checkpoint_promoted':False,'independent_test_queried':False});print('TRAIN025',step,epoch,values,dict(collections.Counter(fams[n] for n in nz)),flush=True);gc.collect()
  if not (HERE/'checkpoints'/f'epoch{epoch:02d}'/'manifest.json').exists():epoch_snapshot(epoch)
 model.requires_grad_(False);arch=tr.e.cr.check_architecture(model,2);arch['backward_passes']=49;arch['limitations']='Qwen-sized Loop/mHC with trained formerly-zero exits and Liquid-inspired temporal operators; not full SenseNova/LFM3';final_hashes={n:tensor_hash(p) for n,p in ps.items()};save('training_complete.json',{'status':'three_epochs_trained_pending_comparison','epochs':3,'optimizer_steps':24,'selected_tensors':292,'selected_values':48340208,'frozen_tensors':407,'all_699_after':final_hashes,'architecture':arch,'seconds':time.monotonic()-start,**memory()});wrapper.close();del wrapper,optimizer,eligible,ps,model,baseline;gc.collect();torch.set_grad_enabled(False)
 restored,_,_=load_variant('epoch3');assert all(tensor_hash(p)==final_hashes[n] for n,p in restored.named_parameters());del restored;gc.collect();save('cold_restore.json',{'epoch':3,'all699_hashes_match':True});save('status.json',{'status':'trained_pending_comparison','optimizer_steps':24,'epochs':3,'model_process_active':False,'checkpoint_promoted':False,'independent_test_queried':False});print('TRAIN025_COMPLETE_COLD_RESTORE_VERIFIED',flush=True)
if __name__=='__main__':main()
