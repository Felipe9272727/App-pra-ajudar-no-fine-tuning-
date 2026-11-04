"""Shared protocol and strict active-architecture checks for the new pilot."""
import hashlib
import collections
import os
import json
from pathlib import Path
import re
import statistics
import sys
import time
import unicodedata

import torch
import torch.nn.functional as F

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'v2_adaptation'))
from experiment import tokenizer,prompt_ids,load_teacher
from native_runtime import load_port,SOURCE_LAYERS
from rsi_cycle import atomic_json,apply_recipe
from modeling_sensenova_loop import execution_plan
from protocol import grade

DATA=json.loads((HERE/'data.json').read_text())
DATA_HASH=hashlib.sha256((HERE/'data.json').read_bytes()).hexdigest()
RECIPE={'gain':0.05,'beta':0.,'liquid_mix':1.}
CPU_THREADS=int(os.environ.get('LS_CPU_THREADS','8'))
assert 1<=CPU_THREADS<=32
torch.set_num_threads(CPU_THREADS)
torch.set_grad_enabled(False)


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def update_status(**kwargs):
    path=HERE/'status.json'
    state=json.loads(path.read_text());state.update(kwargs)
    state['updated_unix']=time.time();atomic_json(path,state)


def architecture_check(model):
    text=model.model.language_model
    layers=text.layers
    cfg=model.config.to_dict()
    plan=execution_plan(cfg)
    assert len(layers)==32 and len(plan)==56
    assert cfg['mhc']['streams']==2
    assert all(float(layer.native_visit_gain[1])>0 for layer in layers[4:28])
    assert all(layer._native_window==256 for i,layer in enumerate(layers) if i in [7,15,27])
    convs=[layer.linear_attn.conv1d.weight for layer in layers if hasattr(layer,'linear_attn')]
    assert all(w.shape[-1]==7 for w in convs)
    nonzero=sum(int(w[:,:,:3].count_nonzero()) for w in convs)
    assert nonzero>0
    assert not any(p.requires_grad for p in model.parameters())
    return {'physical_layers':len(layers),'layer_executions':len(plan),'mhc_streams':2,
        'second_visit_gain':float(layers[4].native_visit_gain[1]),
        'conv_kernel':7,'learned_history_nonzero':nonzero,
        'sliding_window':256,'window_layers':[7,15,27],
        'parameters':sum(p.numel() for p in model.parameters()),'backward_passes':0}


def load_hybrid():
    model=load_port(ROOT,True);apply_recipe(model,RECIPE)
    torch.set_num_threads(CPU_THREADS)
    architecture_check(model)
    return model


def prior_mlp_weight():
    # Reconstructible from the pinned base; the large local cache is optional.
    from safetensors import safe_open
    with safe_open(ROOT/'upstream/model.safetensors-00001-of-00001.safetensors',framework='pt',device='cpu') as f:
        return f.get_tensor(f'model.language_model.layers.{SOURCE_LAYERS[31]}.mlp.down_proj.weight')


@torch.inference_mode()
def apply_edit(model,patch,strength=None):
    if isinstance(patch,(str,Path)):patch=torch.load(patch,weights_only=True)
    assert patch['data_sha256']==DATA_HASH and patch['recipe']==RECIPE
    layer=model.model.language_model.layers[31].mlp.down_proj
    # Restore the SAME existing dense parameter, then write the reconstructed edit.
    base=prior_mlp_weight()
    if 'dense_weight' in patch:
        assert strength is None
        written=patch['dense_weight']
        assert written.shape==base.shape and written.dtype==base.dtype
        delta=written.float()-base.float()
    else:
        strength=patch['strength'] if strength is None else strength
        delta=(patch['left']@patch['right'])*strength
        written=(base.float()+delta).to(base.dtype)
    layer.weight.copy_(written)
    assert torch.isfinite(layer.weight).all()
    return {'changed_bf16_values':int((written.view(torch.int16)!=base.view(torch.int16)).sum()),
        'delta_frobenius':float(delta.norm()),'base_frobenius':float(base.float().norm()),
        'dense_weight_sha256':hashlib.sha256(written.view(torch.uint8).numpy().tobytes()).hexdigest(),
        'runtime_adapter':False,'architecture':architecture_check(model)}


@torch.inference_mode()
def restore_mlp(model):
    model.model.language_model.layers[31].mlp.down_proj.weight.copy_(
        prior_mlp_weight())


@torch.inference_mode()
def likelihood(model,tok,rows,anchors=False):
    # Batch only identical input lengths: no padding or changed position rules.
    buckets=collections.defaultdict(list);out=[None]*len(rows)
    for index,row in enumerate(rows):
        if anchors:
            ids=tok(row,return_tensors='pt',add_special_tokens=False)['input_ids']
            n=min(8,ids.shape[1]-1)
            targets=ids[0,-n:]
        else:
            ids=prompt_ids(tok,row['question'])
            target=tok.encode(row['answer'],add_special_tokens=False)
            ids=torch.cat([ids,torch.tensor([target])],1)
            targets=torch.tensor(target+[tok.eos_token_id])
        buckets[ids.shape[1]].append((index,row,ids,targets))
    for bucket in buckets.values():
        for offset in range(0,len(bucket),4):
            batch=bucket[offset:offset+4]
            keep=max(len(item[3])+(1 if anchors else 0) for item in batch)
            all_logits=model(input_ids=torch.cat([item[2] for item in batch]),
                use_cache=False,logits_to_keep=keep).logits.float()
            for b,(index,row,ids,targets) in enumerate(batch):
                logits=all_logits[b,-len(targets)-1:-1] if anchors else all_logits[b,-len(targets):]
                losses=F.cross_entropy(logits,targets,reduction='none')
                if anchors:
                    out[index]={'nll':float(losses.mean()),'tokens':len(targets)}
                else:
                    out[index]={'id':row['id'],'answer_nll':float(losses[:-1].mean()),
                        'eos_nll':float(losses[-1]),
                        'teacher_forced_answer_token_accuracy':float((logits[:-1].argmax(-1)==targets[:-1]).float().mean())}
    if anchors:return {'mean_nll':statistics.mean(x['nll'] for x in out),'rows':out}
    return {'mean_answer_nll':statistics.mean(x['answer_nll'] for x in out),
        'mean_eos_nll':statistics.mean(x['eos_nll'] for x in out),
        'mean_answer_token_accuracy':statistics.mean(x['teacher_forced_answer_token_accuracy'] for x in out),'rows':out}


def normalized(text):
    text=''.join(c for c in unicodedata.normalize('NFKD',text.casefold()) if not unicodedata.combining(c))
    return re.sub(r'\s+',' ',text).strip().strip(' .!\n`"\'')


@torch.inference_mode()
def generate_rows(model,tok,rows,path,metadata):
    previous=json.loads(path.read_text()) if path.exists() else None
    report={**metadata,'status':'running','data_sha256':DATA_HASH,'rows':[],
        'inference_code_sha256':{str(p.relative_to(ROOT)):file_hash(p) for p in [
            HERE/'common.py',HERE/'protocol.py',ROOT/'v2_adaptation/native_runtime.py',ROOT/'modeling_sensenova_loop.py',ROOT/'rsi_cycle.py']},
        'protocol':{'max_new_tokens':12,'greedy':True,'thinking':False,'use_cache':True,
                    'cpu_threads':torch.get_num_threads(),'backbone':'BF16','routers':'FP32','inference_tools':False,
                    'batching':'at most 4 prompts with exactly the same token length; no padding'}}
    if previous:
        assert previous['data_sha256']==DATA_HASH
        assert previous['variant']==metadata['variant']
        assert previous.get('patch_sha256')==metadata.get('patch_sha256')
        assert previous['inference_code_sha256']==report['inference_code_sha256']
        assert {r['id'] for r in previous['rows']} <= {r['id'] for r in rows}
        if previous['status']=='complete':return previous
        report['rows']=previous['rows']
    completed={r['id'] for r in report['rows']}
    order={r['id']:i for i,r in enumerate(rows)}
    buckets=collections.defaultdict(list)
    for row in rows:
        if row['id'] in completed:continue
        ids=prompt_ids(tok,row['question']);buckets[ids.shape[1]].append((row,ids))
    for bucket in buckets.values():
        for offset in range(0,len(bucket),4):
            batch=bucket[offset:offset+4];start=time.monotonic()
            ids=torch.cat([item[1] for item in batch])
            output=model.generate(input_ids=ids,max_new_tokens=12,do_sample=False,
                use_cache=True,pad_token_id=tok.eos_token_id)[:,ids.shape[1]:]
            seconds=time.monotonic()-start
            for b,(row,_) in enumerate(batch):
                tokens=output[b]
                eos=(tokens==tok.eos_token_id).nonzero()
                if len(eos):tokens=tokens[:int(eos[0])+1]
                text=tok.decode(tokens,skip_special_tokens=True)
                exact,content=grade(text,row)
                report['rows'].append({**row,'output':text,'exact_correct':exact,'content_correct':content,
                    'new_tokens':len(tokens),'hit_limit':len(tokens)==12,
                    'batch_size':len(batch),'batch_seconds':round(seconds,4),
                    'amortized_seconds':round(seconds/len(batch),4)})
                print('GEN',metadata['variant'],row['id'],repr(text),exact,content,flush=True)
            report['rows'].sort(key=lambda r:order[r['id']])
            atomic_json(path,report)
    report.update(status='complete',exact_correct=sum(r['exact_correct'] for r in report['rows']),
                  content_correct=sum(r['content_correct'] for r in report['rows']),total=len(rows))
    atomic_json(path,report)
    return report
