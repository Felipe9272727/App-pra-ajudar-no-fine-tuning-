"""Visit-aware native loop/mHC and LFM3-inspired compatible operators.

This is an experimental hybrid, not the complete LFM3 model. No gradients.
"""
from contextvars import ContextVar
import collections
import json
from pathlib import Path
import sys

import torch
from torch import nn
import torch.nn.functional as F
from safetensors import safe_open

HERE=Path(__file__).resolve().parent
if (HERE.parent/'modeling_sensenova_loop.py').exists():
    sys.path.insert(0,str(HERE.parent))
from modeling_sensenova_loop import (SenseNovaLoopTextModel,MHCDecoderLayer,
    MHCRouter,enter,leave,SenseNovaLoopConfig,SenseNovaLoopForConditionalGeneration)

_VISITS=ContextVar('native_sense_visits',default=None)
SOURCE_GROUPS=[0,1,1,2,3,3,4,5]
SOURCE_LAYERS=[4*g+i for g in SOURCE_GROUPS for i in range(4)]
IDENTITY_LAYERS=set(range(8,12)) | set(range(20,24))
ACTIVE_LINEAR=[i for i in range(4,28)
               if i%4!=3 and i not in IDENTITY_LAYERS]


class NativeTextModel(SenseNovaLoopTextModel):
    def forward(self,*args,**kwargs):
        token=_VISITS.set(collections.Counter())
        try:
            return super().forward(*args,**kwargs)
        finally:
            _VISITS.reset(token)


def window_mask(mask,hidden,positions,cache,window):
    batch,q_len,_=hidden.shape
    if mask is not None:
        k_len=mask.shape[-1]
    elif cache is not None:
        k_len=cache.cache.get_seq_length(cache.virtual)+q_len
    else:
        k_len=q_len
    if positions is None:
        positions=torch.arange(k_len-q_len,k_len,device=hidden.device).view(1,-1)
    q=positions[:,None,:,None]
    k=torch.arange(k_len,device=hidden.device).view(1,1,1,-1)
    allowed=(k<=q)&(k>q-window)
    if mask is not None and mask.dtype==torch.bool:
        return mask & allowed
    if mask is None:
        mask=torch.zeros(batch,1,q_len,k_len,device=hidden.device,dtype=hidden.dtype)
    return mask.masked_fill(~allowed,torch.finfo(mask.dtype).min)


class VisitGatedMHC(MHCDecoderLayer):
    def forward(self,hidden_states,position_embeddings,attention_mask=None,
                position_ids=None,past_key_values=None,**kwargs):
        counts=_VISITS.get()
        if counts is None:
            raise RuntimeError('Visit-aware layer requires NativeTextModel context.')
        physical=self._mhc_physical
        visit=counts[physical]
        counts[physical]+=1
        if visit>1:
            raise ValueError('This experiment supports exactly two visits.')
        self._last_native_visit=visit
        gain=self.native_visit_gain[visit]
        residual=enter(hidden_states,physical,self._mhc_settings)
        branch,post,mix=self.mhc_attn(residual)
        branch=self.input_layernorm(branch)
        kind=self.layer_type if hasattr(self,'layer_type') else self.block_type
        if kind=='linear_attention':
            branch=self.linear_attn(hidden_states=branch,cache_params=past_key_values,
                                    attention_mask=attention_mask,**kwargs)
        else:
            if self._native_window:
                attention_mask=window_mask(attention_mask,branch,position_ids,
                                           past_key_values,self._native_window)
            branch,_=self.self_attn(hidden_states=branch,position_embeddings=position_embeddings,
                attention_mask=attention_mask,position_ids=position_ids,
                past_key_values=past_key_values,**kwargs)
        residual=MHCRouter.merge(residual,branch,post*gain,mix)
        branch,post,mix=self.mhc_ffn(residual)
        branch=self.mlp(self.post_attention_layernorm(branch))
        return leave(MHCRouter.merge(residual,branch,post*gain,mix),
                     physical,self._mhc_settings)


@torch.inference_mode()
def make_native(model,base_file,liquid=False):
    """Undo v1 scaling; make added layers identity; create per-visit weight gates."""
    text=model.model.language_model
    with safe_open(base_file,framework='pt',device='cpu') as source:
        for target,donor in enumerate(SOURCE_LAYERS):
            layer=text.layers[target]
            for suffix,parameter in layer.named_parameters():
                if suffix.startswith(('mhc_','native_')):
                    continue
                name=f'model.language_model.layers.{donor}.{suffix}'
                parameter.copy_(source.get_tensor(name))
            if target in IDENTITY_LAYERS:
                layer.mlp.down_proj.weight.zero_()
                if hasattr(layer,'linear_attn'):
                    layer.linear_attn.out_proj.weight.zero_()
                else:
                    layer.self_attn.o_proj.weight.zero_()
    text.__class__=NativeTextModel
    for i in range(4,28):
        layer=text.layers[i]
        layer.__class__=VisitGatedMHC
        layer.native_visit_gain=nn.Parameter(torch.tensor([1.,0.],dtype=torch.float32),requires_grad=False)
        layer._native_window=256 if liquid and i in [7,15,27] else 0
    if liquid:
        extend_convolutions(model)
    model.requires_grad_(False)
    return model


@torch.inference_mode()
def extend_convolutions(model):
    text=model.model.language_model
    for layer in text.layers:
        if not hasattr(layer,'linear_attn'):
            continue
        block=layer.linear_attn
        old=block.conv1d
        width=old.weight.shape[0]
        conv=nn.Conv1d(width,width,7,groups=width,padding=6,bias=False,
                       dtype=old.weight.dtype,device=old.weight.device)
        conv.weight.copy_(F.pad(old.weight,(7-old.weight.shape[-1],0)))
        conv.requires_grad_(False)
        block.conv1d=conv
        block.conv_kernel_size=7
    for cfg in [model.config.text_config,text.config,text._loop_cache_config]:
        cfg.linear_conv_kernel_dim=7


@torch.inference_mode()
def set_gain(model,value):
    for layer in model.model.language_model.layers[4:28]:
        # Split one nominal residual update across two visits, rather than
        # adding an entire extra update on top of the pretrained computation.
        layer.native_visit_gain[0]=1.-value
        layer.native_visit_gain[1]=value


def load_port(root,liquid=False):
    torch.set_num_threads(8)
    torch.set_grad_enabled(False)
    folder=Path(root)/'sensenova_port'
    cfg=SenseNovaLoopConfig.from_dict(json.loads((folder/'config.json').read_text()))
    model=SenseNovaLoopForConditionalGeneration.from_pretrained(folder,config=cfg,
        local_files_only=True,dtype=torch.bfloat16,attn_implementation='eager').eval()
    return make_native(model,Path(root)/'upstream/model.safetensors-00001-of-00001.safetensors',liquid)
