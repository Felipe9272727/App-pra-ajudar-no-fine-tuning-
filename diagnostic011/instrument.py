"""Forward-only complete raw-parameter access and last-decision activation trace."""
from collections import Counter,defaultdict
from pathlib import Path
import re
import torch
from torch import nn
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_flatten

META={'aten.t.default','aten.transpose.int','aten.permute.default','aten.view.default','aten.reshape.default',
 'aten._unsafe_view.default','aten.unsqueeze.default','aten.squeeze.dim','aten.squeeze.default',
 'aten.select.int','aten.slice.Tensor','aten.detach.default','aten.alias.default','aten.as_strided.default'}
TRANSFORMS={'aten._to_copy.default','aten.clone.default','aten.copy_.default'}
COLS=['input_rms','input_mean','input_absmax','input_zero_fraction','input_nonfinite','input_numel',
      'output_rms','output_mean','output_absmax','output_zero_fraction','output_nonfinite','output_numel']

def first_tensor(args,kwargs=None):
    for key in ['hidden_states','input_ids']:
        if kwargs and isinstance(kwargs.get(key),torch.Tensor):return kwargs[key]
    return next((x for x in tree_flatten(args)[0] if isinstance(x,torch.Tensor)),None)

def last_decision(tensor,module=None):
    if tensor is None:return None
    if tensor.ndim>=3:return tensor[0,-1]
    if tensor.ndim==2:
        if isinstance(module,nn.Embedding):return tensor[0,-1]
        heads=getattr(module,'_diag_last_token_heads',None)
        return tensor[-heads:] if heads else tensor[-1]
    return tensor

def stats(t):
    if t is None:return [float('nan')]*6
    x=t.detach().float().flatten();finite=torch.isfinite(x);valid=x[finite]
    if not len(valid):return [float('nan'),float('nan'),float('nan'),float('nan'),int((~finite).sum()),len(x)]
    return [float(valid.square().mean().sqrt()),float(valid.mean()),float(valid.abs().max()),
      float((valid==0).float().mean()),int((~finite).sum()),len(x)]

class ParameterAccess(TorchDispatchMode):
    def __init__(self,observer):super().__init__();self.o=observer
    def __torch_dispatch__(self,func,types,args=(),kwargs=None):
        o=self.o
        if o.running:
            op=str(func);kind=0 if op in META else (1 if op in TRANSFORMS else 2)
            found=set()
            for value in tree_flatten((args,kwargs or {}))[0]:
                if isinstance(value,torch.Tensor) and value.device.type!='meta':
                    index=o.storage_index.get(value.untyped_storage().data_ptr())
                    if index is not None:found.add(index)
            for index in found:
                o.current_reads[kind][index]+=1;o.operator_counts[index][op]+=1
                if o.stack:
                    slot=o.stack[-1];o.reader_uses[index].add(slot)
                    if kind>=o.reader_priority[index]:o.current_reader[index]=slot;o.reader_priority[index]=kind
        return func(*args,**(kwargs or {}))

class Observer:
    def __init__(self,model,snapshot_steps):
        self.model=model;self.parameters=list(model.named_parameters());self.names=[n for n,p in self.parameters]
        self.canonical={id(p):n for n,p in self.parameters};self.index={n:i for i,n in enumerate(self.names)}
        self.storage_index={p.untyped_storage().data_ptr():i for i,(n,p) in enumerate(self.parameters)}
        self.snapshot_steps=set(snapshot_steps);self.handles=[];self.running=False;self.step=-1;self.stack=[]
        self.operator_counts=defaultdict(Counter);self.reader_uses=defaultdict(set);self.snapshots={}
        self.frames=[];self.read_frames=[];self.reader_frames=[];self.logits=[];self.slots=None;self.moments={}
        self.module_params={};self.module_specs={};self.slot_shapes={};self.frame_context_lengths=[]
        modules=dict(model.named_modules());owners=set()
        for name,module in modules.items():
            local={k:self.canonical[id(p)] for k,p in module.named_parameters(recurse=False)}
            if local:self.module_params[name]=local;owners.add(name)
        # Include physical layers even when they own no direct parameter.
        owners|={name for name in modules if re.fullmatch(r'model.language_model.layers.\d+',name)}
        for name in sorted(owners):
            module=modules[name];self.module_specs[name]={'type':type(module).__name__,'parameters':self.module_params.get(name,{})}
            if name.endswith('linear_attn.norm'):
                module._diag_last_token_heads=modules[name.rsplit('.',1)[0]].num_v_heads
            self.handles.append(module.register_forward_pre_hook(self.pre(name),with_kwargs=True))
            self.handles.append(module.register_forward_hook(self.post(name),with_kwargs=True))
        self.handles.append(model.register_forward_pre_hook(self.begin,with_kwargs=True))
        self.handles.append(model.register_forward_hook(self.end,with_kwargs=True))

    def begin(self,module,args,kwargs):
        self.step+=1;self.running=True;self.stack=[];self.current_events={};self.layer_calls=Counter();self.module_calls=Counter()
        n=len(self.parameters);self.current_reads=[[0]*n for _ in range(3)];self.current_reader=[None]*n;self.reader_priority=[-1]*n
        self.frame_context_lengths.append(int(kwargs['input_ids'].shape[-1]))

    def pre(self,name):
        def hook(module,args,kwargs):
            if not self.running:return
            with torch._C._DisableTorchDispatch():
                if re.fullmatch(r'model.language_model.layers.\d+',name):self.layer_calls[int(name.rsplit('.',1)[1])]+=1
                visit=self.module_calls[name];self.module_calls[name]+=1;slot=(name,visit);self.stack.append(slot)
                raw=first_tensor(args,kwargs);x=last_decision(raw,module)
                self.current_events[slot]=stats(x)+[float('nan')]*6
                if self.step==0:self.slot_shapes.setdefault(slot,{})['input_shape']=list(raw.shape) if raw is not None else None
                if self.step in self.snapshot_steps:
                    self.snapshots.setdefault(self.step,{})[slot]={'input':x.detach().cpu().clone() if x is not None else None}
                effective=None
                if isinstance(module,nn.Linear) and x is not None:effective=x.float().reshape(-1,x.shape[-1])
                elif type(module).__name__=='MHCRouter' and x is not None:
                    v=x.float().flatten();effective=(v*torch.rsqrt(v.square().mean()+1e-6)).view(1,-1)
                if effective is not None:
                    key=slot
                    if key not in self.moments:self.moments[key]={'sum_square':torch.zeros(effective.shape[-1],dtype=torch.float64),'observations':0,'parameter':self.module_params[name].get('weight')}
                    self.moments[key]['sum_square']+=effective.double().square().sum(0);self.moments[key]['observations']+=len(effective)
        return hook

    def post(self,name):
        def hook(module,args,kwargs,output):
            if not self.running:return
            with torch._C._DisableTorchDispatch():
                slot=self.stack[-1];assert slot[0]==name,(slot,name)
                raw=first_tensor(output);x=last_decision(raw,module)
                self.current_events[slot][6:]=stats(x)
                if self.step==0:self.slot_shapes.setdefault(slot,{})['output_shape']=list(raw.shape) if raw is not None else None
                if self.step in self.snapshot_steps:self.snapshots[self.step][slot]['output']=x.detach().cpu().clone() if x is not None else None
                self.stack.pop()
        return hook

    def end(self,module,args,kwargs,output):
        with torch._C._DisableTorchDispatch():
            assert not self.stack
            assert len(self.layer_calls)==32 and sum(self.layer_calls.values())==56
            assert all(self.layer_calls[i]==(2 if 4<=i<28 else 1) for i in range(32))
            keys=sorted(self.current_events)
            if self.slots is None:self.slots=keys;self.slot_index={k:i for i,k in enumerate(keys)}
            assert keys==self.slots,'Module call set changed across cached generation'
            self.frames.append(torch.tensor([self.current_events[k] for k in self.slots],dtype=torch.float32))
            self.read_frames.append(torch.tensor(self.current_reads,dtype=torch.int32))
            self.reader_frames.append(torch.tensor([self.slot_index.get(k,-1) for k in self.current_reader],dtype=torch.int16))
            logit=output.logits[0,-1].detach().float();values,indices=logit.topk(8)
            prob=logit.softmax(-1);entropy=-(prob*prob.clamp_min(1e-30).log()).sum()
            self.logits.append({'top_ids':indices.cpu(),'top_logits':values.cpu(),'entropy':float(entropy),'top_margin':float(values[0]-values[1])})
            self.running=False

    def payload(self):
        assert not self.running
        return {'parameter_names':self.names,'module_specs':self.module_specs,'slots':self.slots,'columns':COLS,
          'per_frame_module_statistics':torch.stack(self.frames),'raw_parameter_access_counts':torch.stack(self.read_frames),
          'access_kind_order':['metadata_view','dtype_copy_transform','mathematical_operator'],
          'parameter_reader_slot':torch.stack(self.reader_frames),'frame_input_lengths':self.frame_context_lengths,
          'slot_prefill_shapes':self.slot_shapes,'snapshots':self.snapshots,'coordinate_moments':self.moments,
          'next_token_statistics':self.logits,'parameter_operator_counts':{self.names[i]:dict(v) for i,v in self.operator_counts.items()},
          'parameter_reader_uses':{self.names[i]:sorted(v) for i,v in self.reader_uses.items()}}

    def close(self):
        for h in self.handles:h.remove()
