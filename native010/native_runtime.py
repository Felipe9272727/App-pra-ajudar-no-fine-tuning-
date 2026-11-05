"""Deterministic native Loop warmstart and hash-checked incremental checkpoints.

Call only after loading the immutable parent. The legacy source loader resets
clone layers, so native overlays must always be applied AFTER that loader.
"""
import hashlib
from collections import Counter
from pathlib import Path
import torch

SOURCE_GROUPS=[0,1,1,2,3,3,4,5]
SOURCE_LAYERS=[4*g+i for g in SOURCE_GROUPS for i in range(4)]
CLONES={i:i-4 for i in list(range(8,12))+list(range(20,24))}
PARENT_HASH='46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'

def tensor_hash(w):
    return hashlib.sha256(w.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()

def attention_projection(layer):
    return layer.linear_attn.out_proj.weight if hasattr(layer,'linear_attn') else layer.self_attn.o_proj.weight

def factor_plan():
    counts=Counter(SOURCE_LAYERS[4:28])
    return {i:1/(2*counts[SOURCE_LAYERS[i]]) for i in range(4,28)}

@torch.inference_mode()
def depth_warmstart(model):
    layers=model.model.language_model.layers
    # Freeze donors before modifying any donor or recipient.
    copies={i:(layers[j].mlp.down_proj.weight.clone(),attention_projection(layers[j]).clone(),
        layers[j].linear_attn.conv1d.weight.clone() if hasattr(layers[j],'linear_attn') else None,
        getattr(layers[j],'_native_window',0)) for i,j in CLONES.items()}
    for i,(mlp,attn,conv,window) in copies.items():
        layers[i].mlp.down_proj.weight.copy_(mlp);attention_projection(layers[i]).copy_(attn)
        if conv is not None:layers[i].linear_attn.conv1d.weight.copy_(conv)
        layers[i]._native_window=window
    for i,factor in factor_plan().items():
        layers[i].mlp.down_proj.weight.mul_(factor);attention_projection(layers[i]).mul_(factor)
        layers[i].native_visit_gain.fill_(1.)
    model.requires_grad_(False)
    return model

def architecture(model):
    text=model.model.language_model;layers=text.layers
    neutral=[i for i,l in enumerate(layers) if not bool(l.mlp.down_proj.weight.count_nonzero())
             and not bool(attention_projection(l).count_nonzero())]
    routers=[getattr(l,k) for l in layers[4:28] for k in ['mhc_attn','mhc_ffn']]
    assert len(layers)==32 and len(text._loop_plan)==56 and not neutral
    assert all(l.native_visit_gain.tolist()==[1.,1.] for l in layers[4:28])
    assert all(l.linear_attn.conv1d.weight.shape[-1]==7 for l in layers if hasattr(l,'linear_attn'))
    assert not any(p.requires_grad for p in model.parameters())
    return {'physical_layers':32,'executions':56,'passes':2,'streams':2,'neutral_layers':neutral,
        'visit_gains':[1.,1.],'projection_factors':factor_plan(),
        'local_windows':{str(i):getattr(l,'_native_window',0) for i,l in enumerate(layers) if hasattr(l,'self_attn')},
        'input_dependent_routers':sum(bool(r.weight.count_nonzero()) for r in routers),
        'history_nonzero':sum(int(l.linear_attn.conv1d.weight[:,:,:3].count_nonzero()) for l in layers if hasattr(l,'linear_attn')),
        'parameters':sum(p.numel() for p in model.parameters()),'backward_passes':0,
        'lineage':'Qwen3.5 widths and DeltaNet; Loop/mHC plus compatible Liquid-inspired kernels; not full LFM3'}

@torch.inference_mode()
def apply_overlay(model,path):
    patch=torch.load(path,map_location='cpu',weights_only=True)
    params=dict(model.named_parameters())
    for name,w in patch.items():
        p=params[name];assert p.shape==w.shape and p.dtype==w.dtype and torch.isfinite(w).all(),name
        p.copy_(w)

def modified_parameters(model,variant):
    keys=set()
    for i in range(4,28):
        prefix=f'model.language_model.layers.{i}.'
        keys|={prefix+'mlp.down_proj.weight',prefix+'native_visit_gain'}
        keys.add(prefix+('linear_attn.out_proj.weight' if hasattr(model.model.language_model.layers[i],'linear_attn') else 'self_attn.o_proj.weight'))
    for i in CLONES:
        if hasattr(model.model.language_model.layers[i],'linear_attn'):keys.add(f'model.language_model.layers.{i}.linear_attn.conv1d.weight')
    if variant in ['liquid','routed']:
        keys|={n for n,p in model.named_parameters() if n.endswith('linear_attn.conv1d.weight')}
    if variant=='routed':keys|={n for n,p in model.named_parameters() if '.mhc_' in n}
    return {n:p for n,p in model.named_parameters() if n in keys}

@torch.inference_mode()
def build(model,variant,folder):
    assert variant in ['depth','liquid','routed']
    depth_warmstart(model);folder=Path(folder)
    if variant in ['liquid','routed']:apply_overlay(model,folder/'checkpoints/liquid.pt')
    if variant=='routed':apply_overlay(model,folder/'checkpoints/routers.pt')
    return architecture(model)

@torch.inference_mode()
def verify_bundle(model,variant,folder):
    import json
    manifest=json.loads((Path(folder)/f'checkpoint_{variant}.json').read_text())
    assert manifest['parent_sha256']==PARENT_HASH
    actual={n:tensor_hash(p) for n,p in modified_parameters(model,variant).items()}
    assert actual==manifest['modified_tensor_hashes'],'Native reconstruction mismatch'
    return actual
