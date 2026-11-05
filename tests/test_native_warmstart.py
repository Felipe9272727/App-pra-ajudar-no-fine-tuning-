import json,sys,unittest,tempfile
from pathlib import Path
from types import SimpleNamespace
from collections import defaultdict
import torch
from torch import nn
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from native010.native_runtime import SOURCE_LAYERS,CLONES,factor_plan,depth_warmstart,apply_overlay,tensor_hash

def toy():
    layers=[]
    for i in range(32):
        l=nn.Module();l.mlp=nn.Module();l.mlp.down_proj=nn.Linear(3,2,bias=False)
        name='linear_attn' if i%4!=3 else 'self_attn';a=nn.Module()
        setattr(a,'out_proj' if name=='linear_attn' else 'o_proj',nn.Linear(2,2,bias=False))
        if name=='linear_attn':a.conv1d=nn.Conv1d(2,2,7,groups=2,bias=False)
        setattr(l,name,a);l.native_visit_gain=nn.Parameter(torch.tensor([.95,.05]));l._native_window=256 if i in [7,15,27] else 0
        with torch.no_grad():
            l.mlp.down_proj.weight.fill_(i+1)
            getattr(a,'out_proj' if name=='linear_attn' else 'o_proj').weight.fill_(2*(i+1))
            if hasattr(a,'conv1d'):a.conv1d.weight.fill_(i+3)
            if i in CLONES:
                l.mlp.down_proj.weight.zero_();getattr(a,'out_proj' if name=='linear_attn' else 'o_proj').weight.zero_()
        layers.append(l)
    model=nn.Module();model.model=nn.Module();model.model.language_model=nn.Module();model.model.language_model.layers=nn.ModuleList(layers)
    return model

class NativeWarmstartTests(unittest.TestCase):
    def test_each_original_donor_has_one_budget_across_copies_and_visits(self):
        budget=defaultdict(float)
        for physical,factor in factor_plan().items():budget[SOURCE_LAYERS[physical]]+=2*factor
        self.assertEqual(len(budget),16);self.assertTrue(all(v==1 for v in budget.values()))
    def test_clone_reads_unscaled_donor_and_preserves_filters_and_windows(self):
        m=toy();l=m.model.language_model.layers;before=l[4].mlp.down_proj.weight.detach().clone();conv=l[4].linear_attn.conv1d.weight.detach().clone()
        depth_warmstart(m)
        self.assertTrue(torch.equal(l[4].mlp.down_proj.weight,before*.25))
        self.assertTrue(torch.equal(l[8].mlp.down_proj.weight,before*.25))
        self.assertTrue(torch.equal(l[8].linear_attn.conv1d.weight,conv))
        self.assertEqual(l[11]._native_window,256)
        self.assertTrue(all(x.native_visit_gain.tolist()==[1.,1.] for x in l[4:28]))
        self.assertFalse(any(p.requires_grad for p in m.parameters()))
    def test_incremental_overlay_roundtrip_exact_and_shape_guard(self):
        a=toy();b=toy();depth_warmstart(a);depth_warmstart(b)
        key='model.language_model.layers.5.linear_attn.conv1d.weight';p=dict(a.named_parameters())[key]
        with torch.no_grad():p.add_(.25)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'patch.pt';torch.save({key:p.detach().clone()},path);apply_overlay(b,path)
            self.assertEqual(tensor_hash(p),tensor_hash(dict(b.named_parameters())[key]))
            torch.save({key:torch.zeros(2)},path)
            with self.assertRaises(AssertionError):apply_overlay(b,path)
    def test_paired_route_logits_preserve_gate_sums_and_mixer_stochasticity(self):
        q=torch.linspace(-.125,.125,100);a=torch.logit(torch.tensor(.25))
        pre=torch.stack([a-.5*q,-a+.5*q],-1).sigmoid();post=2*torch.stack([-q,q],-1).sigmoid()
        self.assertTrue(torch.allclose(pre.sum(-1),torch.ones(100),atol=1e-6));self.assertTrue(torch.allclose(post.sum(-1),torch.ones(100)*2,atol=1e-6))
        self.assertGreater(float((post[:,0]-post[:,1]).abs().max()),0)

if __name__=='__main__':unittest.main()
