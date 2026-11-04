"""Bounded direct-weight proposals; no autograd or reference-token supervision."""
import copy
import torch

def propose(incumbent,baseline,direction,number,seed):
 torch.manual_seed(seed+number)
 child=copy.deepcopy(incumbent);kind=(number-1)%5
 fraction=[.005,.015,.04,.08][int(torch.randint(4,()).item())]
 w=child['dense_weight'].float();base=baseline['dense_weight'].float()
 if kind==0:
  noise=torch.randn(w.shape[1]);v=.5*direction+.5*noise
  v=(v/v.square().mean().sqrt().clamp_min(1e-6)).clamp(-2,2)
  w*=1+fraction*v[None,:];method='activation-informed column perturbation'
 elif kind==1:
  u=torch.randn(w.shape[0]);u/=u.norm()
  v=torch.randn(w.shape[1])+.25*direction;v/=v.norm()
  w+=fraction*base.norm()*u[:,None]*v[None,:];method='rank-one dense write'
 elif kind==2:
  columns=torch.randperm(w.shape[1])[:128]
  w[:,columns]*=1+fraction*torch.sign(torch.randn(len(columns)))[None,:]
  method='sparse neuron-column rescaling'
 elif kind==3:
  for key,h in child['history'].items():
   original=baseline['history'][key].float();noise=torch.randn_like(h.float())
   edited=h.float()+fraction*original.norm()*noise/noise.norm().clamp_min(1e-6)
   delta=edited-original;delta*=min(1.,float(.20*original.norm()/delta.norm().clamp_min(1e-6)))
   child['history'][key]=(original+delta).to(h.dtype)
  method='Liquid historical convolution weights'
 else:
  for key in sorted(child['router_bias']):
   b=child['router_bias'][key];original=baseline['router_bias'][key]
   delta=.015*torch.randn_like(b)
   child['router_bias'][key]=(b+delta).clamp(original-.15,original+.15)
  child['passes']=[2,3,4][int(torch.randint(3,()).item())]
  child['late_gain']=max(.01,min(.20,child['late_gain']+float(torch.randn(()))*.03))
  method='mHC bias weights and positive loop visit gates'
 delta=w-base;delta*=min(1.,float(.08*base.norm()/delta.norm().clamp_min(1e-6)))
 child['dense_weight']=(base+delta).to(incumbent['dense_weight'].dtype)
 child.update(round=number,mutation_seed=seed+number)
 assert torch.isfinite(child['dense_weight']).all()
 return child,{'method':method,'seed':seed+number,'fraction':fraction,'passes':child['passes'],
  'late_gain':child['late_gain'],'dense_relative_norm':float((child['dense_weight'].float()-base).norm()/base.norm()),
  'changed_dense_values_from_incumbent':int((child['dense_weight'].view(torch.int16)!=incumbent['dense_weight'].view(torch.int16)).sum())}
