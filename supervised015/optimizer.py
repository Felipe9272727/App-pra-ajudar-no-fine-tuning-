"""Adafactor applied only after ALL uses of a leaf have accumulated gradients.

Nonreentrant checkpointing and shared/tied weights are verified by preflight.
Release each finished gradient to avoid retaining another full model in RAM.
"""
import torch

def finite(grad):
    return all(bool(torch.isfinite(c).all()) for c in grad.detach().flatten().split(4*1024*1024))

class BackwardAdafactor:
    def __init__(self,parameters,lr=.01,update=True):
        self.parameters=parameters;self.update=update;self.lr=lr;self.round=0
        self.optimizers={name:torch.optim.Adafactor([p],lr=lr,eps=(1e-16,1e-3),
                         beta2_decay=-.8,d=1.,weight_decay=0.,foreach=False) for name,p in parameters.items()} if update else {}
        self.handles=[];self.reset()
        for name,p in parameters.items():
            self.handles.append(p.register_post_accumulate_grad_hook(self.hook(name)))
    def reset(self):self.calls={};self.stats={}
    def hook(self,name):
        def apply(p):
            self.calls[name]=self.calls.get(name,0)+1
            if self.calls[name]!=1:raise RuntimeError('Shared parameter accumulated more than once: '+name)
            grad=p.grad
            if grad is None or not finite(grad):raise RuntimeError('Missing/nonfinite gradient: '+name)
            self.stats[name]={'nonzero':bool(grad.count_nonzero()),'norm':float(grad.norm())}
            if self.update:self.optimizers[name].step()
            p.grad=None
        return apply
    def close(self):
        for h in self.handles:h.remove()
    def state_dict(self):return {name:opt.state_dict() for name,opt in self.optimizers.items()}
    def load_state_dict(self,state):
        for name,opt in self.optimizers.items():opt.load_state_dict(state[name])
