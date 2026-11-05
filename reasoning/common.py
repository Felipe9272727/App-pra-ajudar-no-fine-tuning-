"""Shared direct-parameter overlay; no benchmark identity prompt."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'rsi100'))
os.environ.setdefault('LS_CPU_THREADS','4')
import engine as e
import torch
from local_cpu.sandbox import evaluate
from checkpoint_io import tensor_checkpoint

e.cr.evaluate = evaluate
HERE = ROOT/'reasoning'
PARENT_HASH = '46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'


def save(name, obj):
    e.cr.atomic_json(HERE/name,obj)


@torch.inference_mode()
def load():
    assert e.cr.file_hash(e.CK/'best.pt') == PARENT_HASH
    model,meta = e.cr.load('baseline')
    parent = e.read_checkpoint('best.pt')
    e.apply(model,parent)
    return model,e.cr.tokenizer(),parent,meta


@torch.inference_mode()
def apply(model, parent, patch=None):
    arch = e.apply(model,parent)
    if patch:
        assert patch['parent_sha256']==PARENT_HASH
        if 'dense_weight' in patch:
            target = model.model.language_model.layers[31].mlp.down_proj.weight
            assert patch['dense_weight'].shape==target.shape
            assert patch['dense_weight'].dtype==target.dtype and torch.isfinite(patch['dense_weight']).all()
            target.copy_(patch['dense_weight'])
        for key, values in patch.get('layer_visit_gains',{}).items():
            layer = model.model.language_model.layers[int(key)]
            assert values.shape==layer.native_visit_gain.shape
            assert torch.isfinite(values).all() and bool((values>0).all())
            assert abs(float(values.sum())-1.)<1e-6
            layer.native_visit_gain.copy_(values)
    arch = e.cr.check_architecture(model,parent['passes'])
    arch['layer_visit_gains']={str(i):l.native_visit_gain.tolist()
        for i,l in enumerate(model.model.language_model.layers) if 4<=i<28}
    return arch


def tasks(ids):
    bank={r['id']:r for r in e.DATA['search']+e.DATA['guard']}
    return [bank[k] for k in ids]
