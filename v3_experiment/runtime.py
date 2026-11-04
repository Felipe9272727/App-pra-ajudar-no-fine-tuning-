"""Hybrid-conditioned, parallel coarse-to-fine concept generation.

Every level uses the active SenseNova/Liquid text model. No gold answer,
calculator, autoregressive fallback or retrieval is used by generate().
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import time

import torch
from torch import nn
import torch.nn.functional as F

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'lab_rsi'))
from common import load_hybrid,architecture_check,apply_edit,tokenizer,prompt_ids,file_hash,atomic_json,load_teacher
from codec import ByteConceptCodec,load_codec,LEVELS,SIZES,DIM,WIDTH,STOP

torch.set_num_threads(8);torch.set_grad_enabled(False)
DATA=json.loads((HERE/'data.json').read_text())
DATA_HASH=file_hash(HERE/'data.json')
PARENT_PATCH=ROOT/'lab_rsi/candidate_02.pt'


def fresh_heldout():
    audit=json.loads((HERE/'data_audit.json').read_text())
    assert audit['data_sha256']==DATA_HASH and not audit['heldout_outputs_observed_before_audit']
    excluded=set(audit['excluded_ids'])
    rows=[r for r in DATA['heldout'] if r['id'] not in excluded]
    assert len(rows)==audit['primary_fresh_questions']
    return rows


def status(**kwargs):
    p=HERE/'status.json';state=json.loads(p.read_text()) if p.exists() else {}
    state.update(kwargs,updated_unix=time.time());atomic_json(p,state)


def parent_model():
    model=load_hybrid();write=apply_edit(model,PARENT_PATCH)
    assert write['dense_weight_sha256']=='6a0c8ae0aa485c536d4e3a99b149431c7cad7052e1d5170d704814b3fffad33e'
    return model,write


@torch.inference_mode()
def byte_embeddings(model,tok):
    e=model.model.language_model.embed_tokens.weight
    out=[]
    for b in range(257):
        ids=[tok.eos_token_id] if b==STOP else tok.encode(bytes([b]).decode('latin1'),add_special_tokens=False)
        out.append(e[ids].float().mean(0))
    return torch.stack(out).to(torch.bfloat16)


class NCMExperiment(nn.Module):
    def __init__(self,model,tok,codec,byte_embeds,heads=None):
        super().__init__();self.backbone=model;self.tok=tok;self.codec=codec
        self.byte_embeds=nn.Parameter(byte_embeds,requires_grad=False)
        self.heads=heads
        if heads is not None:
            self.head_weights=nn.ParameterList([nn.Parameter(h['weight'].float(),requires_grad=False) for h in heads])
            for h,w in zip(self.heads,self.head_weights):h['weight']=w
        self.requires_grad_(False).eval()
        architecture_check(model)

    @torch.inference_mode()
    def prefix(self,question):
        ids=prompt_ids(self.tok,question)
        output=self.backbone.model.language_model(input_ids=ids,use_cache=True)
        return output.past_key_values,output.last_hidden_state[:,-1].float(),ids.shape[1]

    @torch.inference_mode()
    def features(self,cache,context,z,level):
        size=LEVELS[level]
        current=self.codec.pooled(z,size)
        scores=self.codec.logits(current)
        probs=(scores/.15).softmax(-1)
        embeds=probs@self.byte_embeds.float()
        marker=self.byte_embeds[ord('?')].float()
        positions=self.byte_embeds[torch.arange(size)+ord('1')].float()
        stage=self.byte_embeds[ord('A')+level].float()
        embeds=marker+.5*embeds+.05*positions+.05*stage
        embeds*=marker.norm()/embeds.norm(dim=-1,keepdim=True).clamp_min(1e-5)
        before=cache.get_seq_length()
        branch=copy.deepcopy(cache)
        output=self.backbone.model.language_model(inputs_embeds=embeds.to(torch.bfloat16),
            past_key_values=branch,use_cache=True)
        assert cache.get_seq_length()==before,'Prefix cache was mutated across levels'
        h=output.last_hidden_state.float()
        pos=F.one_hot(torch.arange(size),WIDTH).float()[None].expand(h.shape[0],-1,-1)
        lev=F.one_hot(torch.tensor(level),len(LEVELS)).float().view(1,1,-1).expand(h.shape[0],size,-1)
        return torch.cat([h,context[:,None,:].expand(-1,size,-1),current*4,pos*2,lev*2],-1)

    @torch.inference_mode()
    def generate(self,question):
        if self.heads is None:raise RuntimeError('Load fitted hierarchy heads first')
        cache,context,length=self.prefix(question)
        z=torch.zeros(1,WIDTH,DIM);trace=[]
        for i,size in enumerate(LEVELS):
            x=self.features(cache,context,z,i)[0]
            head=self.heads[i]
            norm=(x-head['mean'])/head['scale']
            norm=norm/norm.norm(dim=-1,keepdim=True).clamp_min(1e-6)
            target=norm@head['weight'].float()+head['target_mean']
            indices=self.codec.nearest(target[None],i)
            z=self.codec.update(z,indices,i)
            trace.append({'level':i,'positions':size,'codes':indices[0].tolist(),
                          'decoded_draft':self.codec.text(z[0])})
        return self.codec.text(z[0]),{'levels':trace,'parallel_codes':sum(LEVELS),
            'generation_level_passes':len(LEVELS),'prefix_passes':1,'prefix_tokens':length,
            'autoregressive_fallback':False,'backward_passes':0}


def exact_grade(output,row):
    exact=output.strip()==row['answer']
    if row['numeric']:
        import re
        nums=re.findall(r'(?<![\w.])-?\d+(?![\w.])',output.strip().rstrip('.'))
        content=exact or (len(nums)==1 and int(nums[0])==int(row['answer']))
    else:content=exact
    return bool(exact),bool(content)


def byte_accuracy(output,answer):
    expected=list(answer.encode())+[STOP]
    actual=list(output.encode())+[STOP]
    n=min(len(expected),WIDTH)
    return sum(i<len(actual) and actual[i]==expected[i] for i in range(n)),n
