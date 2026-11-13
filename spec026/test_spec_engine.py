"""Scripted stateful unit tests; NOT a model speed or intelligence benchmark."""
import copy
from collections import Counter
import torch
from spec_engine import serial,speculative
class Toy:
 def __init__(self,wrong=-1):self.wrong=wrong;self.counters=Counter();self.v=13
 def reset(self):self.counters.clear()
 def clone(self,c):return copy.deepcopy(c)
 def forward(self,ids,cache=None,all_logits=False):
  values=ids[0].tolist() if torch.is_tensor(ids) else list(ids);cache=[] if cache is None else cache;rows=[]
  for x in values:
   cache.append(x);n=(sum(cache)+len(cache))%self.v
   if self.wrong>=0 and len(cache)%5==self.wrong:n=(n+3)%self.v
   a=torch.full((self.v,),-100.);a[n]=100.;rows.append(a)
  self.counters['calls']+=1;self.counters['evaluated_tokens']+=len(values);return torch.stack(rows if all_logits else rows[-1:]),cache
count=0
for mode in ['block','serial']:
 for wrong in [-1,0,1,2,3,4]:
  for budget in [1,2,3,7,19]:
   t=Toy();d=Toy(wrong);a=serial(t,[2,4],budget,eos=set());b=speculative(t,d,[2,4],budget,4,eos=set(),verify_mode=mode);assert a['ids']==b['ids'],(mode,wrong,budget,a,b);count+=1
for stop in [{3},{5},{7},{0,4,8}]:
 for wrong in [-1,1,3]:
  a=serial(Toy(),[1],24,eos=stop);b=speculative(Toy(),Toy(wrong),[1],24,4,eos=stop);assert a['ids']==b['ids'];count+=1
print({'status':'pending_and_rollback_unit_tests_passed','checks':count,'models_are_synthetic':True})
