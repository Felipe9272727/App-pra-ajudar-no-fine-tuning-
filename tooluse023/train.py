"""One fixed rank32native-cache supervised weight edit from preserved general."""
import copy,gc,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse023';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
from train_runtime import torch,tensor_hash
from transformers import LogitsProcessor,LogitsProcessorList
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(path,obj):tr.e.cr.atomic_json(HERE/path,obj)
def verify():
 for p,h in json.loads((HERE/'frozen.json').read_text()).items():assert sha(ROOT/p)==h,p
def load_general():
 model,tok,parent,meta=tr.load();del parent;return model,tok,meta
@torch.inference_mode()
def collect(model,tok):
 rows=json.loads((HERE/'train.json').read_text());config=json.loads((HERE/'tool_config.json').read_text());data=[];latest={};layer=model.model.language_model.layers[31]
 def xhook(module,args):latest['x']=args[0][0,-1].detach().clone()
 def rhook(module,args):latest['r']=args[0][0,-1].detach().clone()
 def hhook(module,args,out):latest['h']=out[0,-1].detach().clone()
 hooks=[layer.mlp.down_proj.register_forward_pre_hook(xhook),layer.post_attention_layernorm.register_forward_pre_hook(rhook),model.model.language_model.norm.register_forward_hook(hhook)]
 try:
  for i,row in enumerate(rows):
   path=HERE/'cache'/f'{i:02d}.pt'
   if path.exists():d=torch.load(path,weights_only=True);assert d['id']==row['id'];data.append(d);continue
   ids=tok.apply_chat_template(row['messages'],tools=config['schemas'],enable_thinking=False,add_generation_prompt=True,return_dict=False,return_tensors='pt');gold=tok.encode(row['target'],add_special_tokens=False)+[248044];seen=[];preds=[]
   class TeacherOnly(LogitsProcessor):
    def __call__(self,input_ids,scores):
     j=input_ids.shape[1]-ids.shape[1];seen.append((latest['x'],latest['r'],latest['h']));preds.append(int(scores[0].argmax()));out=torch.full_like(scores,float('-inf'));out[0,gold[j]]=0;return out
   out=model.generate(input_ids=ids,max_new_tokens=len(gold),use_cache=True,do_sample=False,pad_token_id=tok.eos_token_id,logits_processor=LogitsProcessorList([TeacherOnly()]))[0,ids.shape[1]:];assert out.tolist()==gold and len(seen)==len(gold)
   d={'id':row['id'],'x':torch.stack([x for x,r,h in seen]),'r':torch.stack([r for x,r,h in seen]),'h_native':torch.stack([h for x,r,h in seen]),'y':torch.tensor(gold),'native_argmax':torch.tensor(preds),'forced_teacher_replay_not_scored':True}
   path.parent.mkdir(exist_ok=True);tmp=path.with_suffix('.tmp');torch.save(d,tmp);tmp.replace(path);data.append(d);print('NATIVE_TEACHER',row['id'],len(gold),flush=True)
 finally:
  for h in hooks:h.remove()
 return {k:torch.cat([d[k] for d in data]) for k in ['x','r','h_native','y','native_argmax']}
@torch.no_grad()
def scan(weight,norm,embedding,data,chunk=32):
 margins=[];competitors=[];preds=[];hidden=[]
 for start in range(0,len(data['y']),chunk):
  h=norm(data['r'][start:start+chunk]+torch.nn.functional.linear(data['x'][start:start+chunk],weight));logits=torch.nn.functional.linear(h,embedding).float();y=data['y'][start:start+chunk];preds.append(logits.argmax(-1));gold=logits.gather(1,y[:,None]).squeeze(1);logits.scatter_(1,y[:,None],float('-inf'));v,c=logits.max(-1);margins.append(gold-v);competitors.append(c);hidden.append(h)
 return torch.cat(margins),torch.cat(competitors),torch.cat(preds),torch.cat(hidden)
def main():
 verify();assert not (HERE/'steps.jsonl').exists() and not (HERE/'checkpoints/final.json').exists(),'Do not repeat or blindly resume partial updates';started=time.monotonic();model,tok,meta=load_general();before={n:tensor_hash(p) for n,p in model.named_parameters()};collected=collect(model,tok)
 assert all(tensor_hash(p)==before[n] for n,p in model.named_parameters());save('parent_integrity.json',{'all699_parent_hashes_verified':True,'tensors':before,'architecture':tr.e.cr.check_architecture(model,2)})
 with torch.inference_mode(False):
  data={k:v.detach().clone() for k,v in collected.items()};old=model.model.language_model.layers[31].mlp.down_proj.weight.detach().clone();embedding=model.lm_head.weight.detach().clone();norm=copy.deepcopy(model.model.language_model.norm);norm.weight=torch.nn.Parameter(norm.weight.detach().clone(),requires_grad=False)
 del model,collected;gc.collect();torch.set_grad_enabled(False);margins,competitors,preds,h=scan(old,norm,embedding,data)
 pre={'tokens':len(margins),'argmax_agreement':float((preds==data['native_argmax']).float().mean()),'max_hidden_reconstruction_error':float((h-data['h_native']).abs().max()),'forced_replay_not_inference_score':True};save('preflight.json',pre);assert pre['argmax_agreement']>=.99 and pre['max_hidden_reconstruction_error']<=.0625,pre;print('PREFLIGHT',json.dumps(pre),flush=True)
 x=data['x'].float();values,vectors=torch.linalg.eigh(x@x.T);u=vectors[:,-32:];a=((x.T@u)/values[-32:].clamp_min(1e-12).sqrt()).T.contiguous().clone();assert torch.allclose(a@a.T,torch.eye(32),atol=1e-3);del x,values,vectors,u
 torch.set_grad_enabled(True);torch.manual_seed(20261123);b=torch.nn.Parameter(torch.zeros(1024,32));optimizer=torch.optim.AdamW([b],lr=.0003,weight_decay=0.);budget=.01*float(old.float().norm());history=[];(HERE/'checkpoints').mkdir(exist_ok=True)
 for step in range(1,33):
  if bool((margins>=.5).all()):break
  optimizer.zero_grad(set_to_none=True);weight=(old.float()+b@a).to(torch.bfloat16);losses=[]
  for start in range(0,len(margins),32):
   hh=norm(data['r'][start:start+32]+torch.nn.functional.linear(data['x'][start:start+32],weight));y=data['y'][start:start+32];c=competitors[start:start+32];selected=torch.stack([embedding[y],embedding[c]],dim=1);pair=torch.bmm(selected,hh.unsqueeze(-1)).squeeze(-1);surrogate=(pair[:,0]-pair[:,1]).float();real=surrogate-surrogate.detach()+margins[start:start+32];losses.append(torch.relu(.5-real).square().sum())
  loss=torch.stack(losses).sum()/len(margins);number=float(loss.detach());loss.backward();assert bool(torch.isfinite(b.grad).all());optimizer.step()
  with torch.no_grad():
   length=float((b@a).norm())
   if length>budget:b.mul_(budget/length)
   merged=(old.float()+b@a).to(torch.bfloat16);margins,competitors,preds,h=scan(merged,norm,embedding,data)
  record={'step':step,'supervised_margin_loss_before_update':number,'cached_correct_tokens':int((preds==data['y']).sum()),'total_teacher_tokens':len(margins),'minimum_margin':float(margins.min()),'relative_float_update':float((b@a).detach().norm()/old.float().norm())};history.append(record)
  with (HERE/'steps.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
  state={'A':a,'B':b.detach(),'optimizer':optimizer.state_dict(),'step':step,'torch_rng':torch.get_rng_state()};tmp=HERE/'checkpoints/latest.tmp';torch.save(state,tmp);tmp.replace(HERE/'checkpoints/latest.pt');print('UPDATE',json.dumps(record),flush=True);del losses,loss,weight;gc.collect()
 with torch.no_grad():merged=(old.float()+b@a).to(torch.bfloat16).contiguous();assert bool(torch.isfinite(merged).all())
 raw=merged.view(torch.uint8).numpy().tobytes();(HERE/'checkpoints/down_proj.bf16.bin').write_bytes(raw);torch.save({'A':a,'B':b.detach(),'parent':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'},HERE/'checkpoints/factors.pt')
 report={'status':'native_cache_training_complete_unvalidated','parent':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8','target':'model.language_model.layers.31.mlp.down_proj.weight','shape':[1024,3584],'dtype':'bfloat16','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'old_tensor_sha256':tensor_hash(old),'updates':len(history),'new_factor_values':147456,'trainable_factor_values':32768,'merged_changed_values':int((merged.view(torch.int16)!=old.view(torch.int16)).sum()),'only_old_tensor_changed':True,'all_other698_tensors_unchanged':True,'all_loop_mhc_temporal_weights_frozen_but_executed':True,'preflight':pre,'seconds':time.monotonic()-started}
 save('checkpoints/final.json',report);print('TRAINING_COMPLETE',json.dumps(report),flush=True)
if __name__=='__main__':main()
