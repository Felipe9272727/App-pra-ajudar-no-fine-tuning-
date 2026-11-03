"""Direct learned weight adaptation without backpropagation.

Calibration uses labeled development plus unlabeled teacher activations.
It IS data-driven adaptation, not a training-free intelligence claim.
The new held-out data never chooses weights or hyperparameters.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import re
import resource
import statistics
import time
import unicodedata

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer,Qwen3_5ForConditionalGeneration
from native_runtime import (load_port,set_gain,extend_convolutions,
    ACTIVE_LINEAR,SOURCE_LAYERS)

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
torch.set_num_threads(8)
torch.set_grad_enabled(False)
torch.manual_seed(20261103)
DATA=json.loads((HERE/'data_v2.json').read_text())
DATA_HASH=hashlib.sha256((HERE/'data_v2.json').read_bytes()).hexdigest()


def save(name,data):
    (HERE/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


def tokenizer():
    return AutoTokenizer.from_pretrained(ROOT/'upstream',local_files_only=True)


def prompt_ids(tok,q):
    return tok.apply_chat_template([{'role':'user','content':q}],tokenize=True,
        return_tensors='pt',return_dict=False,add_generation_prompt=True,enable_thinking=False)


def load_teacher():
    return Qwen3_5ForConditionalGeneration.from_pretrained(ROOT/'upstream',
        local_files_only=True,dtype=torch.bfloat16,attn_implementation='eager').eval().requires_grad_(False)


@torch.inference_mode()
def development_score(model,tok):
    rows=[]
    for row in DATA['development']:
        ids=prompt_ids(tok,row['question'])
        target=tok.encode(row['answer'],add_special_tokens=False)
        whole=torch.cat([ids,torch.tensor([target])],1)
        # Keep the final answer-length+1 logits to avoid a full vocab x sequence buffer.
        logits=model(input_ids=whole,use_cache=False,
                     logits_to_keep=len(target)+1).logits[0,:-1].float()
        nll=F.cross_entropy(logits,torch.tensor(target)).item()
        assert torch.isfinite(logits).all()
        rows.append({'question':row['question'],'answer_nll':nll})
    return {'mean_answer_nll':statistics.mean(r['answer_nll'] for r in rows),'rows':rows}


@torch.inference_mode()
def collect_teacher():
    model=load_teacher();tok=tokenizer()
    source_indices=sorted({SOURCE_LAYERS[i] for i in ACTIVE_LINEAR})
    capture={}
    hooks=[]
    def hook_for(index):
        def hook(module,inputs,output):capture[index]=output.detach().cpu().clone()
        return hook
    for i in source_indices:
        hooks.append(model.model.language_model.layers[i].linear_attn.in_proj_qkv.register_forward_hook(hook_for(i)))
    records=[]
    for i,text in enumerate(DATA['calibration_texts']):
        ids=tok(text,add_special_tokens=False,return_tensors='pt',truncation=True,max_length=64)['input_ids']
        capture.clear()
        model(input_ids=ids,use_cache=False,logits_to_keep=1)
        assert set(capture)==set(source_indices)
        records.append({'ids':ids,'qkv':dict(capture)})
        print('TEACHER_FEATURES',i+1,len(DATA['calibration_texts']),ids.shape[1],flush=True)
    for hook in hooks:hook.remove()
    probes=[]
    for question in ['What is 16 + 23? Reply only with the integer.',
                     'Uma árvore cresce perto de uma casa. Descreva a cena em uma frase.']:
        ids=prompt_ids(tok,question)
        logits=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[0,-1].float()
        probes.append({'ids':ids,'logits':logits.clone()})
    torch.save({'records':records,'probes':probes,'data_sha256':DATA_HASH},HERE/'teacher_features.pt')
    score=development_score(model,tok)
    save('teacher_development.json',score)
    print('TEACHER_DEV',score['mean_answer_nll'],flush=True)


def seven_features(qkv):
    # qkv is batch=1, time, channel. Produce channel, time, past-to-present taps.
    x=qkv[0].transpose(0,1).float()
    return F.pad(x,(6,0)).unfold(1,7,1)


@torch.inference_mode()
def fit_convolutions(model,teacher):
    """Weighted ridge regression, regularized toward the embedded 4-tap prior."""
    text=model.model.language_model
    stats={};priors={}
    for i in ACTIVE_LINEAR:
        prior=text.layers[i].linear_attn.conv1d.weight[:,0].float().clone()
        c=prior.shape[0]
        priors[i]=prior
        stats[i]={'xx':torch.zeros(c,7,7),'xy':torch.zeros(c,7),'yy':torch.zeros(c)}
    current={};hooks=[]
    def hook_for(i):
        layer=text.layers[i]
        def hook(module,inputs,output):
            if layer._last_native_visit!=1:return
            target_qkv=current['record']['qkv'][SOURCE_LAYERS[i]]
            t=seven_features(target_qkv)
            s=seven_features(output)
            y=(t*priors[i][:,None,:]).sum(-1)
            # 90% preserve first-pass computation, 10% align repeated-pass features.
            for x,weight in [(t,9.),(s,1.)]:
                stats[i]['xx'].add_(torch.einsum('cni,cnj->cij',x,x),alpha=weight)
                stats[i]['xy'].add_(torch.einsum('cni,cn->ci',x,y),alpha=weight)
                stats[i]['yy'].add_((y*y).sum(-1),alpha=weight)
        return hook
    for i in ACTIVE_LINEAR:
        hooks.append(text.layers[i].linear_attn.in_proj_qkv.register_forward_hook(hook_for(i)))
    set_gain(model,0.05)
    for j,record in enumerate(teacher['records']):
        current['record']=record
        model(input_ids=record['ids'],use_cache=False,logits_to_keep=1)
        print('CALIBRATION_FEATURES',j+1,len(teacher['records']),flush=True)
    for hook in hooks:hook.remove()
    info=[]
    for i in ACTIVE_LINEAR:
        cov=stats[i]['xx'];rhs=stats[i]['xy'];prior=priors[i]
        ridge=cov.diagonal(dim1=-2,dim2=-1).mean(-1).clamp_min(1e-5)*0.1
        estimate=torch.linalg.solve(cov+ridge[:,None,None]*torch.eye(7),
                                    rhs+ridge[:,None]*prior)
        # A fixed conservative blend, specified before viewing held-out scores.
        written=(prior+0.1*(estimate-prior)).to(torch.bfloat16)
        assert torch.isfinite(written).all()
        before=prior.to(torch.bfloat16)
        text.layers[i].linear_attn.conv1d.weight[:,0].copy_(written)
        def mse(w):
            return (torch.einsum('ci,cij,cj->c',w,cov,w)-2*(w*rhs).sum(-1)+stats[i]['yy']).clamp_min(0).sum().item()
        info.append({'physical_layer':i,'donor':SOURCE_LAYERS[i],
            'changed_bf16_coefficients':int((before.view(torch.int16)!=written.view(torch.int16)).sum()),
            'nonzero_new_history_taps':int((written[:,:3]!=0).sum()),
            'weighted_fit_sse_before':mse(prior),
            'weighted_fit_sse_after':mse(written.float())})
    return {'method':'weighted ridge, analytic solve, prior regularization, 0.1 blend',
            'calibration_texts':len(teacher['records']),'first_pass_weight':9,
            'second_pass_weight':1,'backward_passes':0,'layers':info,
            'changed_coefficients':sum(x['changed_bf16_coefficients'] for x in info),
            'new_history_nonzero':sum(x['nonzero_new_history_taps'] for x in info)}


@torch.inference_mode()
def select_gain(model,tok,name):
    results=[]
    for gain in [0.,0.05,0.25,0.5]:
        set_gain(model,gain)
        scored=development_score(model,tok)
        scored['gain']=gain
        results.append(scored)
        print('DEV_GAIN',name,gain,scored['mean_answer_nll'],flush=True)
    best=min(results,key=lambda x:x['mean_answer_nll'])
    set_gain(model,best['gain'])
    result={'selected_gain':best['gain'],'scores':results,
            'criterion':'development mean answer NLL; no held-out data',
            'first_visit_gain':'1 - selected_gain',
            'second_visit_gain':'selected_gain',
            'extra_loop_updates_active':best['gain']!=0}
    save(name+'_selection.json',result)
    return result


@torch.inference_mode()
def adapt():
    teacher=torch.load(HERE/'teacher_features.pt',weights_only=True)
    assert teacher['data_sha256']==DATA_HASH
    model=load_port(ROOT,False);tok=tokenizer()
    preserved=[]
    for probe in teacher['probes']:
        actual=model(input_ids=probe['ids'],use_cache=False,logits_to_keep=1).logits[0,-1].float()
        expected=probe['logits']
        row={'max_abs_logit_delta':(actual-expected).abs().max().item(),
             'rms_logit_delta':(actual-expected).square().mean().sqrt().item(),
             'same_top_token':actual.argmax().item()==expected.argmax().item()}
        preserved.append(row)
    save('function_preservation.json',preserved)
    print('FUNCTION_PRESERVATION',json.dumps(preserved),flush=True)
    assert all(r['same_top_token'] and r['max_abs_logit_delta']<=0.5 for r in preserved)
    native=select_gain(model,tok,'native')
    # Native checkpoint is represented by its direct gate edits + deterministic replay.
    torch.save({'gain':native['selected_gain']},HERE/'native_patch.pt')
    # Compatible LFM3 motifs: kernel seven and selected 256-token local attention.
    extend_convolutions(model)
    for i in [7,15,27]:model.model.language_model.layers[i]._native_window=256
    fitted=fit_convolutions(model,teacher)
    save('closed_form_fit.json',fitted)
    liquid=select_gain(model,tok,'liquid')
    patch={'gain':liquid['selected_gain'],
           'convolutions':{i:model.model.language_model.layers[i].linear_attn.conv1d.weight.detach().clone()
                           for i in ACTIVE_LINEAR}}
    torch.save(patch,HERE/'liquid_patch.pt')
    save('adaptation_complete.json',{'data_sha256':DATA_HASH,'native':native['selected_gain'],
        'liquid':liquid['selected_gain'],'learned_conv_coefficients_changed':fitted['changed_coefficients'],
        'new_history_nonzero':fitted['new_history_nonzero'],
        'autograd_enabled':torch.is_grad_enabled(),'backward_passes':0,
        'heldout_used':False,'status':'frozen_before_heldout'})


def grade(text,row):
    text=unicodedata.normalize('NFKC',text).strip()
    if row['scoring']=='number':
        # One numeric answer only, optional final full stop. No chain-of-thought extraction.
        if re.fullmatch(r'-?\d+(?:\.\d+)?\.?',text):
            return float(text.rstrip('.'))==float(row['answer'])
        return False
    if row['scoring']=='json':
        try:return json.loads(text)==json.loads(row['answer'])
        except (ValueError,TypeError):return False
    if row['id'] in ['instruction_01','instruction_02','knowledge_04']:
        # Case is part of the requested operation/symbol, not cosmetic here.
        return text.rstrip('.')==row['answer'].rstrip('.')
    return text.casefold().rstrip('.')==row['answer'].casefold().rstrip('.')


@torch.inference_mode()
def benchmark(variant):
    assert (HERE/'adaptation_complete.json').exists(),'Freeze all adaptations first.'
    tok=tokenizer()
    if variant=='original':model=load_teacher()
    else:
        model=load_port(ROOT,variant=='liquid')
        patch=torch.load(HERE/f'{variant}_patch.pt',weights_only=True)
        set_gain(model,patch['gain'])
        if variant=='liquid':
            for i,w in patch['convolutions'].items():
                model.model.language_model.layers[i].linear_attn.conv1d.weight.copy_(w)
    # Cache correctness is a separate short diagnostic, not a fitted objective.
    ids=prompt_ids(tok,'What is 14 + 22? Reply only with the integer.')
    full=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[:,-1].float()
    prefill=model(input_ids=ids[:,:-1],use_cache=True,logits_to_keep=1)
    step=model(input_ids=ids[:,-1:],use_cache=True,past_key_values=prefill.past_key_values,
               logits_to_keep=1).logits[:,-1].float()
    cache={'max_abs_delta':(full-step).abs().max().item(),
           'same_top':full.argmax().item()==step.argmax().item()}
    assert cache['same_top'] and cache['max_abs_delta']<=0.5,cache
    result={'variant':variant,'data_sha256':DATA_HASH,'protocol':{'max_new_tokens':12,
        'thinking':False,'sampling':'greedy','device':'cpu','threads':8,
        'precision':'BF16 backbone; FP32 routing/gains','use_cache':True},
        'cache':cache,'rows':[],'status':'running'}
    if variant!='original':
        result['selected_gain']=float(patch['gain'])
        result['loop_active']=bool(patch['gain'])
        result['liquid_inspired']=variant=='liquid'
    for row in DATA['heldout']:
        ids=prompt_ids(tok,row['question']);begin=time.monotonic()
        output=model.generate(input_ids=ids,do_sample=False,max_new_tokens=12,
            use_cache=True,pad_token_id=tok.eos_token_id)
        new=output[0,ids.shape[1]:]
        text=tok.decode(new,skip_special_tokens=True)
        scored={**row,'output':text,'correct':grade(text,row),
                'new_tokens':len(new),'hit_limit':len(new)==12,
                'seconds':round(time.monotonic()-begin,4)}
        result['rows'].append(scored)
        save('test_'+variant+'.json',result)
        print('TEST',variant,row['id'],repr(text),scored['correct'],flush=True)
    result['status']='complete'
    result['correct']=sum(r['correct'] for r in result['rows'])
    result['total']=len(result['rows'])
    result['peak_rss_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    save('test_'+variant+'.json',result)
    print('COMPLETE',variant,result['correct'],result['total'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['teacher','adapt','original','native','liquid'])
    args=p.parse_args()
    if args.stage=='teacher':collect_teacher()
    elif args.stage=='adapt':adapt()
    else:benchmark(args.stage)
