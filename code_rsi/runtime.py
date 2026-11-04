"""Weight-edit experiment runtime; prompts never include test oracles."""
import collections
import copy
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'code_rsi'
sys.path.insert(0,str(ROOT/'lab_rsi'))
from common import load_hybrid,load_teacher,tokenizer,file_hash,likelihood,grade
from rsi_cycle import atomic_json
from modeling_sensenova_loop import execution_plan
from native_runtime import SOURCE_LAYERS
from loop_protocol import VARIANTS,visit_gains
from sandbox import evaluate,extract_code
import torch
from torch import nn
DATA=json.loads((HERE/'data.json').read_text());DATA_HASH=file_hash(HERE/'data.json')
THREADS=int(os.environ.get('LS_CPU_THREADS','4'));torch.set_num_threads(THREADS);torch.set_grad_enabled(False)
assert THREADS==4


def state(**kw):
    p=HERE/'status.json';obj=json.loads(p.read_text());obj.update(kw);obj['updated_unix']=time.time();atomic_json(p,obj)

def source_hashes():
    paths=['code_rsi/runtime.py','code_rsi/checkpoint_io.py','code_rsi/sandbox.py','code_rsi/loop_protocol.py','v2_adaptation/native_runtime.py','modeling_sensenova_loop.py','rsi_cycle.py']
    return {p:file_hash(ROOT/p) for p in paths}

def configure_loops(model,passes,gains=None):
    text=model.model.language_model;gains=visit_gains(passes) if gains is None else gains
    assert len(gains)==passes and all(g>0 for g in gains) and abs(sum(gains)-1)<1e-6
    model.config.loop_settings={**model.config.loop_settings,'eval_count':passes,'counts':[passes]}
    text._loop_plan=execution_plan(model.config.to_dict())
    text._loop_cache_config=copy.deepcopy(text.config)
    text._loop_cache_config.num_hidden_layers=len(text._loop_plan)
    text._loop_cache_config.layer_types=[text.config.layer_types[i] for i in text._loop_plan]
    for layer in text.layers[4:28]:
        layer.native_visit_gain=nn.Parameter(torch.tensor(gains,dtype=torch.float32),requires_grad=False)
    return check_architecture(model,passes)

def check_architecture(model,passes):
    text=model.model.language_model
    assert len(text.layers)==32 and len(text._loop_plan)==8+24*passes
    assert model.config.mhc['streams']==2
    assert all(len(l.native_visit_gain)==passes and bool((l.native_visit_gain>0).all()) for l in text.layers[4:28])
    convs=[l.linear_attn.conv1d.weight for l in text.layers if hasattr(l,'linear_attn')]
    assert all(w.shape[-1]==7 for w in convs)
    nonzero=sum(int(w[:,:,:3].count_nonzero()) for w in convs);assert nonzero>0
    assert all(text.layers[i]._native_window==256 for i in [7,15,27])
    assert not any(p.requires_grad for p in model.parameters())
    return {'passes':passes,'layer_executions':len(text._loop_plan),'physical_layers':32,
        'mhc_streams':2,'visit_gain_weights':text.layers[4].native_visit_gain.tolist(),
        'conv_kernel':7,'learned_history_nonzero':nonzero,'local_window':256,
        'loaded_parameters':sum(p.numel() for p in model.parameters()),'backward_passes':0,
        'limitations':'Qwen widths/weights, mHC routers initialized; eight inserted layers neutral; not full SenseNova/LFM3'}


def load(variant):
    if variant=='original':
        model=load_teacher();torch.set_num_threads(THREADS);return model,{'variant':'original','loaded_parameters':sum(p.numel() for p in model.parameters())}
    assert variant in VARIANTS
    model=load_hybrid();spec=VARIANTS[variant]
    metadata={'variant':variant,'recipe':{'gain':.05,'beta':0.,'liquid_mix':1.},'patch_sha256':None}
    if spec['edit']:
        path=HERE/'checkpoints'/f'{variant}.pt'
        patch=torch.load(path,weights_only=True)
        assert patch['data_sha256']==DATA_HASH and patch['passes']==spec['passes']
        base=model.model.language_model.layers[31].mlp.down_proj.weight
        written=patch['dense_weight'];assert written.shape==base.shape and written.dtype==base.dtype and torch.isfinite(written).all()
        metadata['changed_bf16_values']=int((written.view(torch.int16)!=base.view(torch.int16)).sum())
        base.copy_(written);metadata['patch_sha256']=file_hash(path)
        metadata['architecture']=configure_loops(model,patch['passes'],patch['loop_gain_weights'])
    else:metadata['architecture']=configure_loops(model,2)
    return model,metadata


def prompt(tok,text,thinking=False):
    return tok.apply_chat_template([{'role':'user','content':text}],tokenize=True,
        return_tensors='pt',return_dict=False,add_generation_prompt=True,enable_thinking=thinking)


@torch.inference_mode()
def generate(model,tok,text,max_tokens=160,capture=False,thinking=False,seed=0):
    ids=prompt(tok,text,thinking);hooks=[];xs=[];visits=collections.defaultdict(list)
    if capture:
        def xhook(module,inputs):xs.append(inputs[0][0,-1].detach().float().abs().cpu())
        hooks.append(model.model.language_model.layers[31].mlp.down_proj.register_forward_pre_hook(xhook))
        for index in [7,15,27]:
            def hook(module,inputs,output,index=index):
                if inputs[0].shape[1]>1:
                    visits[index].append(output[0,-1].detach().float().flatten().cpu())
            hooks.append(model.model.language_model.layers[index].register_forward_hook(hook))
    started=time.monotonic()
    try:
        torch.manual_seed(seed)
        opts={'do_sample':False}
        if thinking:opts={'do_sample':True,'temperature':.6,'top_p':.95,'top_k':20}
        out=model.generate(input_ids=ids,max_new_tokens=max_tokens,use_cache=True,
            pad_token_id=tok.eos_token_id,**opts)[0,ids.shape[1]:]
    finally:
        for hook in hooks:hook.remove()
    trace={}
    if capture:
        trace['mlp_mean_abs_input']=torch.stack(xs).mean(0)
        trace['prefill_visit_diagnostics']={}
        for index,states in visits.items():
            a=states[0];b=states[-1]
            trace['prefill_visit_diagnostics'][str(index)]={'visits':len(states),
                'relative_last_first_drift':float((b-a).norm()/a.norm().clamp_min(1e-6)),
                'first_norm':float(a.norm()),'last_norm':float(b.norm()),
                'cosine':float(torch.nn.functional.cosine_similarity(a,b,dim=0))}
    return {'output':tok.decode(out,skip_special_tokens=True),'new_tokens':len(out),
        'hit_limit':len(out)==max_tokens,'seconds':time.monotonic()-started,
        'thinking':thinking,'trace':trace}


@torch.inference_mode()
def cache_check(model,tok,passes):
    ids=prompt(tok,'Write function solve(xs) returning the length of xs. Return only the function.')
    full=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[:,-1].float()
    pre=model(input_ids=ids[:,:-1],use_cache=True,logits_to_keep=1)
    step=model(input_ids=ids[:,-1:],past_key_values=pre.past_key_values,use_cache=True,logits_to_keep=1).logits[:,-1].float()
    diagnostic={'max_abs_delta':float((full-step).abs().max()),'same_top_token':bool(full.argmax()==step.argmax()),'passes':passes}
    assert diagnostic['same_top_token'] and diagnostic['max_abs_delta']<=.5,diagnostic
    return diagnostic


def fresh_report(variant,split,meta):
    return {**meta,'variant':variant,'split':split,'status':'running','data_sha256':DATA_HASH,
        'inference_code_sha256':source_hashes(),'protocol':{'max_new_tokens':160,'greedy':True,
        'thinking':False,'cpu_threads':THREADS,'pass_at_1':True,'feedback_at_evaluation':False,
        'sandbox_image':os.environ.get('CODE_IMAGE'),'test_answers_in_prompt':False},'rows':[]}


@torch.inference_mode()
def evaluate_rows(model,tok,rows,path,report):
    if path.exists():
        old=json.loads(path.read_text());assert old['data_sha256']==DATA_HASH and old['variant']==report['variant']
        assert old['inference_code_sha256']==report['inference_code_sha256']
        assert old['protocol']==report['protocol'] and old.get('patch_sha256')==report.get('patch_sha256')
        assert {r['id'] for r in old['rows']}<={r['id'] for r in rows}
        report=old
    seen={r['id'] for r in report['rows']}
    for row in rows:
        if row['id'] in seen:continue
        out=generate(model,tok,row['prompt'])
        out.pop('trace');scored=evaluate(out['output'],row)
        report['rows'].append({'id':row['id'],**out,**scored})
        atomic_json(path,report)
        print('CODE',report['variant'],row['id'],scored['category'],scored['passed'],scored['total'],flush=True)
    report.update(status='complete',tasks_passed=sum(r['all_passed'] for r in report['rows']),
        tests_passed=sum(r['passed'] for r in report['rows']),tests_total=sum(r['total'] for r in report['rows']),
        total=len(rows),failure_categories=dict(collections.Counter(r['category'] for r in report['rows'])))
    atomic_json(path,report);return report


@torch.inference_mode()
def controls(model,tok,split):
    rows=[]
    for row in DATA['controls'][split]:
        out=generate(model,tok,row['question'],max_tokens=32);exact,content=grade(out['output'],row)
        rows.append({**row,'output':out['output'],'exact_correct':exact,'new_tokens':out['new_tokens']})
    return {'correct':sum(r['exact_correct'] for r in rows),'total':len(rows),'rows':rows}
