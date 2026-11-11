"""Frozen, supervised closed-form loop adapters; serial request-local history.

New weights operate inside the existing physical loop exit (layer 27), on visit
two only. Temporal features are a causal seven-tap filter, not a full LFM model.
The original Loop/mHC/DeltaNet operators and every parent weight remain intact.
"""
import hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; HERE=ROOT/'review013'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,e,torch,PARENT_HASH,tensor_checkpoint
from local_cpu.sandbox import evaluate

def save(path,obj):e.cr.atomic_json(HERE/path,obj)
def filehash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rms(x):return x.float().square().mean(-1,keepdim=True).sqrt().clamp_min(1e-6)
def temporal(x,history=None):
    """Seven causal exponential taps, left zero padding; matches chunked decode."""
    history=x.new_zeros((x.shape[0],6,x.shape[-1])) if history is None else history
    joined=torch.cat([history,x.float()],dim=1)
    weights=x.new_tensor([2.**i for i in range(7)],dtype=torch.float32)/127
    filtered=sum(weights[i]*joined[:,i:i+x.shape[1]] for i in range(7))
    return x.float()-filtered,joined[:,-6:].detach().clone()

def features(first,current,history=None):
    d=current.float()-first.float();t,history=temporal(current.float(),history)
    return torch.cat([d/rms(d),t/rms(t)],dim=-1),history

class Review(torch.nn.Module):
    def __init__(self,patch):
        super().__init__()
        self.input_basis=torch.nn.Parameter(patch['input_basis'].float(),requires_grad=False)
        self.output_map=torch.nn.Parameter(patch['output_map'].float(),requires_grad=False)
        self.kind=patch['kind'];self.cap=float(patch['cap']);self.reset()
    def reset(self):self.first=None;self.history=None;self.calls=0;self.update_sum=0.;self.update_max=0.
    def forward(self,first,current):
        f,self.history=features(first,current,self.history)
        if self.kind=='loop':f=f[...,:1024]
        y=(f@self.input_basis)@self.output_map
        y=y*torch.clamp(self.cap/rms(y),max=1)
        delta=y*rms(current)
        ratio=float((rms(delta)/rms(current)).mean())
        self.calls+=1;self.update_sum+=ratio;self.update_max=max(self.update_max,ratio)
        return (current.float()+delta).to(current.dtype)

class Installed:
    def __init__(self,model,patch):
        self.model=model;self.module=Review(patch);model.add_module('supervised_loop_review',self.module)
        self.layer=model.model.language_model.layers[27]
        self.handles=[model.register_forward_pre_hook(self.before,with_kwargs=True),self.layer.register_forward_hook(self.after)]
    def before(self,module,args,kwargs):
        cache=kwargs.get('past_key_values')
        if cache is None or cache.get_seq_length()==0:self.module.reset()
    def after(self,module,args,out):
        if module._last_native_visit==0:self.module.first=out.detach().clone()
        else:
            assert module._last_native_visit==1,'Adapter trained for two visits only'
            assert self.module.first is not None and self.module.first.shape==out.shape
            return self.module(self.module.first,out)
    def close(self):
        for h in self.handles:h.remove()
        delattr(self.model,'supervised_loop_review')
    def stats(self):
        r=self.module
        return {'review_calls':r.calls,'mean_update_rms_fraction':r.update_sum/max(1,r.calls),
                'max_mean_update_rms_fraction':r.update_max,'adapter_parameters':sum(p.numel() for p in r.parameters()),
                'first_visit_unchanged_by_placement':True,'temporal_features':r.kind=='joint'}

def load_variant(kind):
    if kind=='original':
        model,meta=e.cr.load('original');return model,e.cr.tokenizer(),meta,None
    model,tok,parent,meta=load();installed=None
    if kind in ('loop','joint'):
        path=HERE/'checkpoints'/(kind+'.pt');patch=torch.load(path,weights_only=True)
        assert patch['parent_sha256']==PARENT_HASH
        installed=Installed(model,patch);meta['adapter_sha256']=filehash(path)
    return model,tok,meta,installed

def verify_frozen():
    frozen=json.loads((HERE/'frozen.json').read_text())
    for path,h in frozen.items():assert filehash(ROOT/path)==h,path

def eval_inputs(row):
    """Return ONLY the problem statement. Never pass solution/cases to generation."""
    return row['prompt']
