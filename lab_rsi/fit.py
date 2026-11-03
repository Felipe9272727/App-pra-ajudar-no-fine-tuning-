"""Closed-form edits to an existing dense MLP; no gradients, no runtime adapter.

Local first-order logit-margin residuals are regressed on MLP features.
The approximation can fail; held-out generations, not the fit loss, test it.
"""
import argparse
import json
from pathlib import Path
import time

import torch
from common import *


@torch.inference_mode()
def collect():
    path=HERE/'features.pt'
    if path.exists():
        saved=torch.load(path,weights_only=True)
        assert saved['data_sha256']==DATA_HASH
        print('REUSE_FEATURES',flush=True);return
    update_status(status='collecting_train_features',phase='closed_form_learning')
    model=load_hybrid();tok=tokenizer()
    layer=model.model.language_model.layers[31].mlp.down_proj
    torch.save({'weight':layer.weight.detach().clone()},HERE/'last_mlp_prior.pt')
    capture={}
    def hook_x(module,inputs):capture['x']=inputs[0].detach().float().clone()
    def hook_h(module,inputs):capture['h']=inputs[0].detach().float().clone()
    handles=[layer.register_forward_pre_hook(hook_x),
             model.model.language_model.norm.register_forward_pre_hook(hook_h)]
    norm=model.model.language_model.norm
    normscale=1+norm.weight.float()
    xs=[];ys=[];stops=[];wrong=0;target_count=0;stats=[]
    for i,row in enumerate(DATA['train']):
        ids=prompt_ids(tok,row['question']);target=tok.encode(row['answer'],add_special_tokens=False)
        whole=torch.cat([ids,torch.tensor([target])],1);n=len(target)+1
        logits=model(input_ids=whole,use_cache=False,logits_to_keep=n).logits[0].float()
        targets=torch.tensor(target+[tok.eos_token_id])
        x=capture['x'][0,-n:];h=capture['h'][0,-n:]
        assert x.shape==(n,layer.weight.shape[1]) and h.shape==(n,layer.weight.shape[0])
        pred=logits.argmax(-1);iswrong=pred!=targets
        y=torch.zeros_like(h)
        for j in range(n):
            if not iswrong[j]:continue
            v=(model.lm_head.weight[targets[j]].float()-model.lm_head.weight[pred[j]].float())*normscale
            # RMSNorm Jacobian direction, projected off the radial component.
            v-=h[j]*(torch.dot(v,h[j])/h[j].square().sum().clamp_min(1e-8))
            rms=(h[j].square().mean()+norm.eps).sqrt()
            gap=(logits[j,pred[j]]-logits[j,targets[j]]+0.5).clamp_min(0)
            delta=gap*rms*v/v.square().sum().clamp_min(1e-8)
            cap=0.05*h[j].norm()
            delta*=min(1.,float(cap/delta.norm().clamp_min(1e-8)))
            y[j]=delta
        xs.append(x);ys.append(y);stops.extend([False]*len(target)+[True])
        wrong+=int(iswrong.sum());target_count+=n
        stats.append({'id':row['id'],'tokens':n,'wrong_teacher_forced_tokens':int(iswrong.sum())})
        if (i+1)%8==0:
            print('TRAIN_FEATURES',i+1,len(DATA['train']),'wrong',wrong,'/',target_count,flush=True)
            update_status(status='collecting_train_features',train_examples_done=i+1)
    n_train=sum(len(x) for x in xs)
    for text in DATA['anchors']:
        ids=tok(text,return_tensors='pt',add_special_tokens=False)['input_ids']
        model(input_ids=ids,use_cache=False,logits_to_keep=1)
        x=capture['x'][0,-8:]
        xs.append(x);ys.append(torch.zeros(len(x),layer.weight.shape[0]));stops.extend([False]*len(x))
    for handle in handles:handle.remove()
    features={'x':torch.cat(xs),'y':torch.cat(ys),'is_stop':torch.tensor(stops),
        'n_train_columns':n_train,'data_sha256':DATA_HASH,'recipe':RECIPE,
        'architecture':architecture_check(model)}
    torch.save(features,path)
    atomic_json(HERE/'fit_metadata.json',{'training_examples':len(DATA['train']),
        'training_token_positions':n_train,'anchor_positions':len(features['x'])-n_train,
        'wrong_token_positions':wrong,'train_rows':stats,'backward_passes':0,
        'method':'RMSNorm linearized logit-margin residual + regularized closed-form least squares',
        'layer':'model.language_model.layers.31.mlp.down_proj.weight',
        'residual_cap_fraction_of_hidden_norm':0.05,'architecture':features['architecture'],
        'data_sha256':DATA_HASH,'feature_sha256':file_hash(path)})
    print('FEATURES_SAVED',tuple(features['x'].shape),tuple(features['y'].shape),flush=True)


@torch.inference_mode()
def fit():
    features=torch.load(HERE/'features.pt',weights_only=True)
    assert features['data_sha256']==DATA_HASH and features['recipe']==RECIPE
    x=features['x'].T.contiguous();y=features['y'].T.contiguous()
    meta=json.loads((HERE/'fit_metadata.json').read_text())
    changed_targets=y.norm(dim=0)>0
    meta['wrong_digit_positions']=int((changed_targets & ~features['is_stop']).sum())
    meta['wrong_stop_positions']=int((changed_targets & features['is_stop']).sum())
    atomic_json(HERE/'fit_metadata.json',meta)
    scale=x.norm(dim=0).clamp_min(1e-5)
    xn=x/scale;yn=y/scale
    # Columns with zero desired residual are preservation anchors, not discarded.
    gram=xn.T@xn
    prior=torch.load(HERE/'last_mlp_prior.pt',weights_only=True)['weight']
    archive=[]
    for i,recipe in enumerate(DATA['protocol']['candidates']):
        key=f'candidate_{i+1:02d}'
        mask=torch.ones(y.shape[1],dtype=torch.bool)
        if recipe['family']=='digits':mask &= ~features['is_stop']
        elif recipe['family']=='stop_only':mask &= features['is_stop']
        wanted=yn*mask
        ridge=recipe['ridge']
        solved=torch.linalg.solve(gram+ridge*torch.eye(gram.shape[0]),xn.T)
        dense=wanted@solved
        # Compression only; factors are multiplied into the original dense matrix.
        torch.manual_seed(701)
        u,s,v=torch.svd_lowrank(dense,q=40,niter=3)
        rank=32;left=u[:,:rank]*s[:rank];right=v[:,:rank].T
        compressed=left@right
        maxnorm=.1*prior.float().norm()
        normcap=min(1.,float(maxnorm/compressed.norm().clamp_min(1e-8)))
        left*=normcap
        patch={**recipe,'left':left.contiguous(),'right':right.contiguous(),
            'data_sha256':DATA_HASH,'recipe':RECIPE,'rank':rank,
            'layer':31,'target':'mlp.down_proj.weight','dense_norm_cap':normcap,
            'runtime_adapter':False,'backward_passes':0}
        path=HERE/f'{key}.pt';torch.save(patch,path)
        record={**recipe,'id':key,'patch':str(path.relative_to(ROOT)),
            'patch_sha256':file_hash(path),'rank':rank,'norm_cap_scale':normcap,
            'compression_relative_error':float((dense-compressed).norm()/dense.norm().clamp_min(1e-8)),
            'status':'awaiting_development','selected_by':'assistant preregistered candidate program',
            'hypothesis':{'joint':'Improve answer-token and stop margins inside active hybrid',
              'digits':'Improve answer content while preserving stop behavior',
              'stop_only':'Negative control: test whether gains are only response formatting'}[recipe['family']]}
        archive.append(record)
        print('FIT',key,recipe,'delta_norm',float((left@right).norm()),flush=True)
    atomic_json(HERE/'archive.json',{'data_sha256':DATA_HASH,'candidates':archive})
    update_status(status='candidates_fitted',candidates_fitted=len(archive),train_examples_done=96)


@torch.inference_mode()
def develop():
    from likelihood_cache import build_cache,score_cache
    archive=json.loads((HERE/'archive.json').read_text())
    model=load_hybrid();tok=tokenizer()
    update_status(status='preparing_exact_screening_cache')
    devcache=build_cache(model,tok,DATA['development'],HERE/'development_cache.pt')
    anchorcache=build_cache(model,tok,DATA['anchors'],HERE/'anchor_cache.pt',True)
    replaybase={'answer':score_cache(model,devcache),'anchors':score_cache(model,anchorcache),
                'architecture':architecture_check(model)}
    basepath=HERE/'development_baseline.json'
    if basepath.exists():
        base=json.loads(basepath.read_text())
        assert abs(base['answer']['mean_answer_nll']-replaybase['answer']['mean_answer_nll'])<1e-7
        assert abs(base['anchors']['mean_nll']-replaybase['anchors']['mean_nll'])<1e-7
    else:
        base=replaybase
        atomic_json(basepath,base)
    for completed in archive['candidates']:
        if completed['status']!='development_complete':continue
        apply_edit(model,ROOT/completed['patch'])
        check=score_cache(model,devcache)
        assert abs(check['mean_answer_nll']-completed['development']['mean_answer_nll'])<1e-7
    atomic_json(HERE/'screening_cache_check.json',{'baseline_max_logit_delta':max(
        devcache['max_replay_logit_delta'],anchorcache['max_replay_logit_delta']),
        'baseline_nll_delta':replaybase['answer']['mean_answer_nll']-base['answer']['mean_answer_nll'],
        'completed_candidate_nll_matches':True,'final_generation_uses_full_model':True})
    for candidate in archive['candidates']:
        if candidate['status']!='awaiting_development':continue
        update_status(status='development_evaluation',evaluating_candidate=candidate['id'])
        written=apply_edit(model,ROOT/candidate['patch'])
        scored=score_cache(model,devcache)
        anchors=score_cache(model,anchorcache)
        passes=scored['mean_answer_nll']<base['answer']['mean_answer_nll']-1e-4
        preserves=anchors['mean_nll']<=base['anchors']['mean_nll']*1.1
        candidate.update(status='development_complete',development=scored,anchor=anchors,
            passes_answer_nll=passes,passes_anchor=preserves,weight_write=written,
            validation_eligible=passes and preserves and candidate['family']!='stop_only')
        atomic_json(HERE/'archive.json',archive)
        print('DEV',candidate['id'],'answer_nll',scored['mean_answer_nll'],
              'baseline',base['answer']['mean_answer_nll'],'anchors',anchors['mean_nll'],
              'eligible',candidate['validation_eligible'],flush=True)
    eligible=sorted([c for c in archive['candidates'] if c['validation_eligible']],
                    key=lambda c:c['development']['mean_answer_nll'])[:2]
    atomic_json(HERE/'validation_queue.json',{'candidate_ids':[c['id'] for c in eligible],
        'criterion':DATA['protocol']['selection'],'heldout_used':False})
    update_status(status='awaiting_validation',validation_queue=[c['id'] for c in eligible],evaluating_candidate=None)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['collect','fit','develop'])
    phase=p.parse_args().phase
    {'collect':collect,'fit':fit,'develop':develop}[phase]()
