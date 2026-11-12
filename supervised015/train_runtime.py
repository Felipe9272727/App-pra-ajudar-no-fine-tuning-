"""Full text-parameter supervision with visit-correct activation checkpointing.

The immutable parent loader was written for inference. Materialize ordinary
parameters/buffers before enabling autograd; keep tied aliases tied. Checkpoint
each physical execution with its explicit visit context, including recomputation.
"""
import collections,gc,hashlib,json,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'supervised015'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,e,torch,PARENT_HASH
import native_runtime as native
from torch.utils.checkpoint import checkpoint
from native010.native_runtime import tensor_hash

def save(name,value):e.cr.atomic_json(HERE/name,value)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def text_parameter(name):return name.startswith('model.language_model.') or name.startswith('lm_head.')

def materialize(model):
    aliases={};buffers={}
    with torch.inference_mode(False):
        for _,module in model.named_modules():
            for name,p in list(module._parameters.items()):
                if p is None:continue
                key=id(p)
                if key not in aliases:aliases[key]=torch.nn.Parameter(p.detach().clone(),requires_grad=False)
                module._parameters[name]=aliases[key]
            for name,b in list(module._buffers.items()):
                if b is None:continue
                key=id(b)
                if key not in buffers:buffers[key]=b.detach().clone()
                module._buffers[name]=buffers[key]
    assert model.get_input_embeddings().weight is model.get_output_embeddings().weight
    gc.collect()

class CheckpointVisits:
    def __init__(self,model):
        self.originals=[];self.calls=collections.Counter()
        for physical,layer in enumerate(model.model.language_model.layers):
            original=layer.forward;self.originals.append((layer,original))
            layer.gradient_checkpointing=False
            layer.forward=types.MethodType(self.make_wrapper(physical,original),layer)
    def make_wrapper(self,physical,original):
        owner=self
        def wrapped(layer,hidden,*args,**kwargs):
            if not layer.training or not torch.is_grad_enabled():return original(hidden,*args,**kwargs)
            counts=native._VISITS.get()
            visit=counts[physical] if 4<=physical<28 else 0
            if 4<=physical<28:counts[physical]+=1
            def run(h):
                token=native._VISITS.set(collections.Counter({physical:visit}))
                owner.calls[(physical,visit)]+=1
                try:return original(h,*args,**kwargs)
                finally:native._VISITS.reset(token)
            return checkpoint(run,hidden,use_reentrant=False,preserve_rng_state=True)
        return wrapped
    def close(self):
        for layer,original in self.originals:layer.forward=original

def enable_training(model):
    torch.set_grad_enabled(True)
    model.train();model.model.visual.eval()
    for name,p in model.named_parameters():p.requires_grad_(text_parameter(name))
    eligible={name:p for name,p in model.named_parameters() if p.requires_grad}
    assert len(eligible)==546
    assert sum(p.numel() for p in eligible.values())==919659696
    return eligible

def encode(tok,row):
    prompt=e.cr.prompt(tok,row['prompt']);answer=tok.encode(row['solution']+tok.eos_token,add_special_tokens=False)
    ids=torch.cat([prompt,torch.tensor([answer])],dim=1)
    return ids[:,:-1],torch.tensor(answer)

def loss(model,ids,gold,chunk=16):
    hidden=model.model(input_ids=ids,use_cache=False).last_hidden_state[0,-len(gold):]
    losses=[]
    def head_ce(h,y):
        logits=torch.nn.functional.linear(h,model.get_output_embeddings().weight)
        return torch.nn.functional.cross_entropy(logits.float(),y,reduction='sum')
    for start in range(0,len(gold),chunk):
        h=hidden[start:start+chunk];y=gold[start:start+chunk]
        losses.append(checkpoint(head_ce,h,y,use_reentrant=False,preserve_rng_state=True))
    return torch.stack(losses).sum()/len(gold)

@torch.no_grad()
def project_gains(model):
    for layer in model.model.language_model.layers[4:28]:
        g=layer.native_visit_gain;g.clamp_(min=1e-4);g.div_(g.sum())

def load_trainable():
    model,tok,parent,meta=load();materialize(model)
    eligible=enable_training(model);wrapper=CheckpointVisits(model)
    return model,tok,meta,eligible,wrapper
