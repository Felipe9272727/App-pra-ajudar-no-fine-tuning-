"""Select hypotheses and an equally-sized activity-matched random control."""
import math,random,statistics

def choose_channels(code,prose,k,seed):
 if len(code)!=len(prose) or len(code)<2*k:raise ValueError('Invalid feature dimensions')
 if any(not math.isfinite(x) or x<0 for x in code+prose):raise ValueError('Invalid activation statistic')
 positive=[x for x in code if x>0]
 if len(positive)<2*k:raise ValueError('Not enough active channels')
 floor=statistics.median(positive)
 active=[i for i,x in enumerate(code) if x>=floor]
 scores=[math.log((a+1e-6)/(b+1e-6)) for a,b in zip(code,prose)]
 selected=sorted(active,key=lambda i:(-scores[i],i))[:k]
 if len(selected)!=k:raise ValueError('Not enough candidate channels')
 available=set(range(len(code)))-set(selected);control=[];rng=random.Random(seed)
 for i in selected:
  near=sorted(available,key=lambda j:(abs(math.log(code[j]+1e-6)-math.log(code[i]+1e-6)),j))[:16]
  j=rng.choice(near);control.append(j);available.remove(j)
 return selected,control,scores

def write_columns(weight,indices,columns):
 """Write an existing parameter, not a detached advanced-indexing result."""
 weight.index_copy_(1,indices,columns)
