"""All-parameter from-scratch learning; no target weights, no held-out prompts."""
import argparse,collections,gc,json,math,time,types
from pathlib import Path
import torch
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint
from transformers.models.qwen3_5 import modeling_qwen3_5 as hf
_original_training_chunk=hf.torch_chunk_gated_delta_rule
def fp32_gdn_core(*args,**kwargs):
 with torch.autocast("cpu",enabled=False):return _original_training_chunk(*args,**kwargs)
hf.torch_chunk_gated_delta_rule=fp32_gdn_core
from draft_model import DraftLM,native_visit,tensor_hash
from io_parts import save_json,save_parts,file_hash
H=Path(__file__).resolve().parent
class Visits:
 def __init__(self,model):
  self.saved=[];self.calls=collections.Counter()
  for i,l in enumerate(model.model.language_model.layers):
   old=l.forward;self.saved.append((l,old));l.gradient_checkpointing=False;l.forward=types.MethodType(self.wrap(i,old),l)
 def wrap(self,i,old):
  owner=self
  def wrapped(layer,hidden,*args,**kw):
   if not layer.training or not torch.is_grad_enabled():return old(hidden,*args,**kw)
   counts=native_visit._VISITS.get();visit=counts[i] if 4<=i<28 else 0
   if 4<=i<28:counts[i]+=1
   def run(x):
    token=native_visit._VISITS.set(collections.Counter({i:visit}));owner.calls[(i,visit)]+=1
    try:return old(x,*args,**kw)
    finally:native_visit._VISITS.reset(token)
   return checkpoint(run,hidden,use_reentrant=False,preserve_rng_state=True)
  return wrapped
 def close(self):
  for l,old in self.saved:l.forward=old

def mem():
 s=Path('/proc/self/status').read_text();return {k:int(s.split(label+':')[1].split()[0]) for k,label in [('rss_kb','VmRSS'),('peak_rss_kb','VmHWM')]}
def control(n,p):return '.mhc_' in n or 'native_visit_gain' in n or p.ndim<2

def loss(model,ids,labels):
 embedding=model.get_input_embeddings()(ids).to(torch.bfloat16);o=model.model(inputs_embeds=embedding,use_cache=False);h=o.last_hidden_state.reshape(-1,o.last_hidden_state.shape[-1]);y=labels.reshape(-1);mask=y!=-100;h=h[mask];y=y[mask];values=[]
 def ce(x,gold):return F.cross_entropy(model.logits(x).float(),gold,reduction='sum')
 for start in range(0,len(y),32):values.append(checkpoint(ce,h[start:start+32],y[start:start+32],use_reentrant=False,preserve_rng_state=True))
 return torch.stack(values).sum()/len(y)

def main():
 frozen=json.loads((H/'frozen.json').read_text());assert all(file_hash(H.parent/n)==v for n,v in frozen.items()),'Frozen source/data mismatch';a=argparse.ArgumentParser();a.add_argument('size',choices=['small','large']);arg=a.parse_args();cfg=json.loads((H/'config.json').read_text());packed=json.loads((H/'data/packed_manifest.json').read_text());assert file_hash(H/'data/packed.pt.bin')==packed['packed_sha256'];folder=H/'checkpoints'/arg.size;log=H/'logs'/f'training_{arg.size}.jsonl';assert not log.exists(),'Inspect existing optimizer/rolling state before restart';assert not (folder/'final/manifest.json').exists();torch.set_num_threads(4);torch.set_grad_enabled(True);started=time.monotonic();model=DraftLM(arg.size,cfg['seed']);model.train();ps=dict(model.named_parameters());assert all(p.dtype==torch.float32 for p in ps.values());save_json(folder/'model_config.json',model.config.to_dict());assert sum(p.numel() for p in ps.values())==cfg['expected_parameters'][arg.size];initial={n:tensor_hash(p) for n,p in ps.items()};audit=model.audit();save_json(H/'reports'/f'initial_{arg.size}.json',{'architecture':audit,'parameter_hashes':initial,'random_initialization':True,'pretrained_tensor_copies':0});save_parts(folder/'initial',{'model':model.state_dict(),'seed':cfg['seed'],'size':arg.size,'step':0},{'phase':'initial_FP32','size':arg.size,'parameters':audit['unique_parameters'],'teacher_weights_copied':False});print('INITIAL_SAVED',arg.size,audit['unique_parameters'],flush=True)
 data=torch.load(H/'data/packed.pt.bin',weights_only=True);ids=data['input_ids'];labels=data['labels'];wrapped=Visits(model);groups=[{'params':[p for n,p in ps.items() if not control(n,p)],'lr':cfg['lr_matrix']},{'params':[p for n,p in ps.items() if control(n,p)],'lr':cfg['lr_controls']}];opt=torch.optim.Adafactor(groups,eps=(1e-16,1e-3),beta2_decay=-.8,d=1.,weight_decay=0.,foreach=False)
 with torch.autocast('cpu',dtype=torch.bfloat16):v=loss(model,ids[:1],labels[:1])
 v.backward();present=[n for n,p in ps.items() if p.grad is not None];nonzero=[n for n,p in ps.items() if p.grad is not None and bool(p.grad.count_nonzero())];assert len(present)==len(ps),set(ps)-set(present);assert all(bool(torch.isfinite(p.grad).all()) for p in ps.values());assert all(wrapped.calls[(i,j)]>=2 for i in range(4,28) for j in [0,1]);assert all(tensor_hash(p)==initial[n] for n,p in ps.items());save_json(H/'reports'/f'backward_{arg.size}.json',{'status':'no_update_preflight_passed','loss':float(v.detach()),'all_parameters_have_gradients':True,'nonzero_gradient_tensor_count':len(nonzero),'all_parameter_tensors':len(ps),'both_actual_visits_recomputed':True,'all_initial_hashes_unchanged':True,**mem()});opt.zero_grad(set_to_none=True);del v;gc.collect();step=0;seen=0;epoch_stats=[];ever=set()
 for epoch in range(1,cfg['epochs']+1):
  order=torch.randperm(len(ids),generator=torch.Generator().manual_seed(cfg['seed']+epoch)).tolist();total=0.;count=0
  for start in range(0,len(order),cfg['batch_size']):
   batch=order[start:start+cfg['batch_size']];step+=1;warm=cfg['warmup_steps'];end=packed['optimizer_steps_per_size'];factor=step/warm if step<=warm else cfg['lr_final_fraction']+(1-cfg['lr_final_fraction'])*.5*(1+math.cos(math.pi*(step-warm)/max(1,end-warm)));opt.param_groups[0]['lr']=cfg['lr_matrix']*factor;opt.param_groups[1]['lr']=cfg['lr_controls']*factor;opt.zero_grad(set_to_none=True)
   with torch.autocast('cpu',dtype=torch.bfloat16):v=loss(model,ids[batch],labels[batch])
   number=float(v.detach());assert math.isfinite(number);v.backward();assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in ps.values());nz={n for n,p in ps.items() if bool(p.grad.count_nonzero())};ever.update(nz);norm=float(torch.nn.utils.clip_grad_norm_(model.parameters(),cfg['gradient_clip']));opt.step()
   with torch.no_grad():
    for l in model.model.language_model.layers[4:28]:l.native_visit_gain.clamp_(min=1e-4);l.native_visit_gain.div_(l.native_visit_gain.sum())
   nt=int((labels[batch]!=-100).sum());seen+=nt;total+=number*nt;count+=nt;entry={'step':step,'epoch':epoch,'tokens':nt,'cumulative_tokens':seen,'nll_before_update':number,'gradient_norm_before_clip':norm,'nonzero_gradient_tensors':len(nz),'lr_factor':factor,'seconds':time.monotonic()-started,**mem()}
   with log.open('a') as f:f.write(json.dumps(entry)+'\n')
   if step%5==0 or step==1:print('SCRATCH026',arg.size,step,end,number,seen,flush=True)
   del v;gc.collect()
  e={'epoch':epoch,'mean_online_train_nll':total/count,'tokens':count};epoch_stats.append(e);save_json(H/'reports'/f'epochs_{arg.size}.json',epoch_stats);opt.zero_grad(set_to_none=True);rolling=Path('/dev/shm/liquid-spec026')/f'rolling_{arg.size}.pt';tmp=rolling.with_suffix('.tmp');torch.save({'model':model.state_dict(),'optimizer':opt.state_dict(),'rng':torch.get_rng_state(),'step':step,'seed':cfg['seed'],'size':arg.size},tmp);tmp.replace(rolling);print('EPOCH026',arg.size,epoch,e['mean_online_train_nll'],flush=True)
 assert seen==packed['training_token_presentations_per_size'];assert step==packed['optimizer_steps_per_size'];assert all(bool(torch.isfinite(p).all()) for p in ps.values());final={n:tensor_hash(p) for n,p in ps.items()};opt.zero_grad(set_to_none=True);save_parts(folder/'final',{'model':model.state_dict(),'optimizer':opt.state_dict(),'rng':torch.get_rng_state(),'step':step,'seed':cfg['seed'],'size':arg.size},{'phase':'trained_FP32_with_optimizer','size':arg.size,'steps':step,'training_tokens':seen,'parameters':audit['unique_parameters']});wrapped.close();del wrapped,opt;gc.collect();model.inference_bf16();inference_hashes={n:tensor_hash(p) for n,p in model.named_parameters()};m=save_parts(folder/'inference',{'model':model.state_dict(),'step':step,'seed':cfg['seed'],'size':arg.size},{'phase':'BF16_inference_FP32_routers_gains','size':arg.size,'steps':step,'parameters':audit['unique_parameters']});save_json(H/'reports'/f'training_{arg.size}.json',{'status':'trained_from_scratch','architecture':model.audit(),'optimizer_steps':step,'epochs':cfg['epochs'],'training_tokens':seen,'unique_conversations':packed['unique_conversations'],'all_eligible_parameter_tensors':len(ps),'changed_parameter_tensors':sum(initial[n]!=final[n] for n in initial),'all_finite':True,'nonzero_gradient_name_union':sorted(ever),'final_FP32_hashes':final,'inference_hashes':inference_hashes,'initial_hashes_source':f'initial_{arg.size}.json','teacher_weights_copied':False,'tokenizer_shared':True,'epochs_online_NLL':epoch_stats,'seconds_descriptive':time.monotonic()-started,'inference_compressed_bytes':m['compressed_bytes'],**mem()});print('SCRATCH026_COMPLETE',arg.size,step,seen,flush=True)
if __name__=='__main__':main()
