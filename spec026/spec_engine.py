"""Greedy pending-token speculation, full-cache rollback and explicit cost counters."""
import copy,time
from collections import Counter
import torch
from transformers.models.qwen3_5 import modeling_qwen3_5 as hf
EOS={248044,248046}
_ORIGINAL_CHUNK=hf.torch_chunk_gated_delta_rule

def install_cached_recurrent_rule():
 # Cached blocks follow the same time recurrence as serial cached decode.
 # Uncached prefill is unchanged. Projection/attention batching still needs parity checks.
 def cached(*args,**kw):
  if kw.get('initial_state') is not None:return hf.torch_recurrent_gated_delta_rule(*args,**kw)
  return _ORIGINAL_CHUNK(*args,**kw)
 hf.torch_chunk_gated_delta_rule=cached

class Engine:
 def __init__(self,model,name):self.model=model;self.name=name;self.counters=Counter()
 def reset(self):self.counters.clear()
 def clone(self,cache):
  t=time.perf_counter();r=copy.deepcopy(cache);self.counters['clone_seconds']+=time.perf_counter()-t;return r
 def forward(self,ids,cache=None,all_logits=False):
  if not torch.is_tensor(ids):ids=torch.tensor([ids],dtype=torch.long)
  t=time.perf_counter()
  o=self.model.model(input_ids=ids,past_key_values=cache,use_cache=True)
  h=o.last_hidden_state[0] if all_logits else o.last_hidden_state[0,-1:]
  logits=torch.nn.functional.linear(h,self.model.get_output_embeddings().weight).float();self.counters['seconds']+=time.perf_counter()-t;self.counters['calls']+=1;self.counters['evaluated_tokens']+=ids.shape[1]
  return logits,o.past_key_values

def argmax(x):return int(x.argmax(-1))
@torch.inference_mode()
def serial(engine,prompt,budget,eos=EOS):
 engine.reset();t=time.perf_counter();logits,cache=engine.forward(prompt);prefill=time.perf_counter()-t;out=[]
 for i in range(budget):
  token=argmax(logits[-1]);out.append(token)
  if token in eos or i+1==budget:break
  logits,cache=engine.forward([token],cache)
 total=time.perf_counter()-t
 return {'ids':out,'seconds':total,'prefill_seconds':prefill,'decode_seconds':total-prefill,'first_token_seconds':prefill,'target':dict(engine.counters),'tokens':len(out),'draft':{},'proposed':0,'accepted':0}

@torch.inference_mode()
def speculative(target,draft,prompt,budget,block=4,eos=EOS,verify_mode='block'):
 assert block>=1 and budget>=1;target.reset();draft.reset();t=time.perf_counter();logits,tc=target.forward(prompt);prefill=time.perf_counter()-t;out=[argmax(logits[-1])];trace=[];proposed=accepted=rejects=0
 if out[-1] in eos or budget==1:return {'ids':out,'seconds':time.perf_counter()-t,'prefill_seconds':prefill,'decode_seconds':0.,'first_token_seconds':prefill,'target':dict(target.counters),'draft':{},'tokens':len(out),'proposed':0,'accepted':0,'trace':trace}
 _,dc=draft.forward(prompt)
 while len(out)<budget:
  pending=out[-1];remaining=budget-len(out)
  if remaining==1:
   z,tc=target.forward([pending],tc);out.append(argmax(z[-1]));break
  k=min(block,remaining-1);ts=target.clone(tc);ds=draft.clone(dc);dl,dc=draft.forward([pending],dc);ys=[]
  for j in range(k):
   y=argmax(dl[-1]);ys.append(y);dl,dc=draft.forward([y],dc)
   if y in eos:break
  proposed+=len(ys)
  if verify_mode=='block':z,trial=target.forward([pending]+ys,tc,all_logits=True)
  else:
   scores=[];trial=tc
   for y in [pending]+ys:
    q,trial=target.forward([y],trial);scores.append(q[-1])
   z=torch.stack(scores)
  n=0
  for i,y in enumerate(ys):
   expected=argmax(z[i])
   if y!=expected:break
   out.append(y);accepted+=1;n+=1
   if y in eos or len(out)==budget:break
  entry={'drafted':len(ys),'accepted':n,'all_accepted':n==len(ys)};trace.append(entry)
  if out[-1] in eos or len(out)>=budget:tc=trial;break
  if n==len(ys):
   tc=trial;out.append(argmax(z[-1]))
  else:
   rejects+=1;tc=ts;dc=ds
   # Prefix-state replay is REAL work. The correction remains pending until next block.
   if verify_mode=='block':_,tc=target.forward([pending]+ys[:n],tc,all_logits=True)
   else:
    for y in [pending]+ys[:n]:_,tc=target.forward([y],tc)
   for y in [pending]+ys[:n]:_,dc=draft.forward([y],dc)
   out.append(argmax(z[n]))
  if out[-1] in eos:break
 total=time.perf_counter()-t
 return {'ids':out,'tokens':len(out),'seconds':total,'prefill_seconds':prefill,'decode_seconds':total-prefill,'first_token_seconds':prefill,'target':dict(target.counters),'draft':dict(draft.counters),'proposed':proposed,'accepted':accepted,'acceptance':accepted/proposed if proposed else 0.,'rejection_blocks':rejects,'trace':trace,'verify_mode':verify_mode,'pending_final_token_not_processed_same_as_serial':True}
