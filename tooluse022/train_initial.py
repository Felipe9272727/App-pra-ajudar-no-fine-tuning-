"""Fixed8-update supervised residual readout; every old parameter is frozen."""
import argparse,gc,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse022';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
from train_runtime import torch,tensor_hash
def save(path,obj):tr.e.cr.atomic_json(HERE/path,obj)
def filehash(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify():
 for p,h in json.loads((HERE/'data_frozen.json').read_text()).items():assert filehash(ROOT/p)==h,p
def load_e():
 from supervised015.attempt_e.restore import load_d
 model,tok,meta,m=load_d();assert m['stream_sha256']=='33f4d2b0fa0d36329ec0bd59d94ca9054c5c4ab549b7a551743a955711679b85';return model,tok,meta
@torch.inference_mode()
def collect(model,tok):
 rows=json.loads((HERE/'train.json').read_text());config=json.loads((HERE/'tool_config.json').read_text());xx=[];yy=[];groups=[];progress=[]
 for i,row in enumerate(rows):
  path=HERE/'cache'/f'{i:02d}.pt'
  if path.exists():
   d=torch.load(path,weights_only=True);assert d['id']==row['id'];xx.append(d['h']);yy.append(d['y']);groups.extend([i]*len(d['y']));continue
  ids=tok.apply_chat_template(row['messages'],tools=config['schemas'],enable_thinking=False,add_generation_prompt=True,return_tensors='pt',return_dict=False);y=tok.encode(row['target']+tok.eos_token,add_special_tokens=False);assert y[-1]==248044
  tokens=torch.cat([ids,torch.tensor([y[:-1]])],dim=1);assert tokens.shape[1]<=4096
  h=model.model(input_ids=tokens,use_cache=False).last_hidden_state[0,-len(y):].contiguous().clone();assert h.shape==(len(y),1024)
  data={'id':row['id'],'h':h,'y':torch.tensor(y),'input_sha256':hashlib.sha256(tokens.numpy().tobytes()).hexdigest(),'forced_teacher_replay_not_scored':True}
  path.parent.mkdir(exist_ok=True);tmp=path.with_suffix('.tmp');torch.save(data,tmp);tmp.replace(path);xx.append(h);yy.append(data['y']);groups.extend([i]*len(y));print('COLLECTED',row['id'],len(y),flush=True)
 return torch.cat(xx),torch.cat(yy),torch.tensor(groups)
def main():
 verify();assert not (HERE/'checkpoints/final.pt').exists(),'Completed weights exist; do not retrain';assert not (HERE/'steps.jsonl').exists(),'Inspect partial optimizer state before resuming'
 start=time.monotonic();model,tok,meta=load_e();before={n:tensor_hash(p) for n,p in model.named_parameters()};h0,y0,groups0=collect(model,tok)
 assert all(tensor_hash(p)==before[n] for n,p in model.named_parameters());save('old_tensor_integrity.json',{'all_old699_tensors_unchanged':True,'tensors':before,'architecture':tr.e.cr.check_architecture(model,2)})
 with torch.inference_mode(False):h=h0.clone();y=y0.clone();groups=groups0.clone();embedding=model.lm_head.weight.detach().clone()
 del model,h0,y0,groups0;gc.collect();torch.set_grad_enabled(True);torch.manual_seed(20261122)
 _,vectors=torch.linalg.eigh(h.float().T@h.float());a=vectors[:,-32:].T.contiguous().detach();b=torch.nn.Parameter(torch.zeros(1024,32));optimizer=torch.optim.AdamW([b],lr=.002,weight_decay=0.)
 order=torch.randperm(len(y));history=[];(HERE/'checkpoints').mkdir(exist_ok=True)
 for step in range(1,9):
  idx=order[((step-1)*64+torch.arange(64))%len(order)];hh=h[idx];target=y[idx];optimizer.zero_grad(set_to_none=True)
  adapted=(hh.float()+torch.nn.functional.linear(torch.nn.functional.linear(hh.float(),a),b)).to(torch.bfloat16)
  logits=torch.nn.functional.linear(adapted,embedding).float();loss=torch.nn.functional.cross_entropy(logits,target);loss.backward();assert bool(torch.isfinite(b.grad).all());optimizer.step()
  record={'step':step,'full_vocabulary_cross_entropy_before_update':float(loss.detach()),'batch_tokens':64,'trainable_new_values':b.numel(),'B_frobenius':float(b.detach().norm()),'taught_data_only':True};history.append(record)
  with (HERE/'steps.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
  state={'A':a,'B':b.detach(),'optimizer':optimizer.state_dict(),'step':step,'rng':torch.get_rng_state(),'parent_E_stream':'33f4d2b0fa0d36329ec0bd59d94ca9054c5c4ab549b7a551743a955711679b85'};tmp=HERE/'checkpoints/latest.tmp';torch.save(state,tmp);tmp.replace(HERE/'checkpoints/latest.pt');print('UPDATE',json.dumps(record),flush=True);del logits,loss,adapted;gc.collect()
 torch.save({'A':a,'B':b.detach(),'parent_E_stream':state['parent_E_stream'],'placement':'after_final_norm_before_tied_lm_head','rank':32},HERE/'checkpoints/final.pt')
 report={'status':'fixed_training_complete_not_validated','updates':8,'new_values':a.numel()+b.numel(),'trainable_new_values':b.numel(),'all_old699_tensors_unchanged':True,'training_tokens':len(y),'teaching_traces':8,'supervised_turns':16,'cache_mode':'full_prefill_teacher_forcing_not_generation_score','checkpoint_sha256':filehash(HERE/'checkpoints/final.pt'),'seconds':time.monotonic()-start,'history':history,'source_metadata':meta,'no_general_superiority_claim':True};save('training_complete.json',report);print('TRAINING_COMPLETE',report['checkpoint_sha256'],flush=True)
if __name__=='__main__':main()
