"""One resumable, assistant-guided improvement cycle with actual weight edits.

The small model suggests; the assistant controller chooses a validated recipe.
Development evaluates proposals. Held-out data never promotes a candidate.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import torch
from safetensors import safe_open

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'v2_adaptation'))
from native_runtime import load_port,set_gain,SOURCE_LAYERS
from experiment import development_score,prompt_ids,tokenizer

torch.set_grad_enabled(False)
torch.set_num_threads(8)


def atomic_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    with temp.open('w') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False)
        f.flush();os.fsync(f.fileno())
    temp.replace(path)


def validate(recipe):
    if set(recipe)!={'gain','beta','liquid_mix'}:raise ValueError('Unexpected recipe fields')
    for name,lo,hi in [('gain',0.,0.5),('beta',0.,0.5),('liquid_mix',0.,1.)]:
        value=recipe[name]
        if type(value) not in [int,float] or not lo<=value<=hi:
            raise ValueError(f'Invalid {name}')


@torch.inference_mode()
def apply_recipe(model,recipe):
    validate(recipe)
    text=model.model.language_model
    set_gain(model,recipe['gain'])
    # Rebuild original/inserted output matrices directly from pinned Qwen tensors.
    # Beta splits a donor's residual contribution between two physical copies.
    with safe_open(ROOT/'upstream/model.safetensors-00001-of-00001.safetensors',
                   framework='pt',device='cpu') as original:
        for primary,added in [(4,8),(16,20)]:
            for offset in range(4):
                a,b=primary+offset,added+offset
                donor=SOURCE_LAYERS[a]
                kind='linear_attn.out_proj.weight' if offset!=3 else 'self_attn.o_proj.weight'
                for suffix in ['mlp.down_proj.weight',kind]:
                    tensor=original.get_tensor(f'model.language_model.layers.{donor}.{suffix}')
                    left=dict(text.layers[a].named_parameters())[suffix]
                    right=dict(text.layers[b].named_parameters())[suffix]
                    left.copy_((tensor.float()*(1.-recipe['beta'])).to(tensor.dtype))
                    right.copy_((tensor.float()*recipe['beta']).to(tensor.dtype))
    # Every candidate uses seven-tap storage; mix zero is exactly the 4-tap prior.
    patch=torch.load(ROOT/'checkpoints/liquid_patch.pt',weights_only=True)
    with safe_open(ROOT/'upstream/model.safetensors-00001-of-00001.safetensors',
                   framework='pt',device='cpu') as original:
        for target,layer in enumerate(text.layers):
            if not hasattr(layer,'linear_attn'):continue
            donor=SOURCE_LAYERS[target]
            prior=torch.nn.functional.pad(original.get_tensor(
                f'model.language_model.layers.{donor}.linear_attn.conv1d.weight'),(3,0))
            learned=patch['convolutions'].get(target,prior)
            mixed=(prior.float()+recipe['liquid_mix']*(learned.float()-prior.float())).to(prior.dtype)
            layer.linear_attn.conv1d.weight.copy_(mixed)
        for i in [7,15,27]:
            text.layers[i]._native_window=256 if recipe['liquid_mix']>0 else 0
    assert all(not p.requires_grad for p in model.parameters())


@torch.inference_mode()
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--round',type=int,required=True)
    p.add_argument('--gain',type=float,required=True)
    p.add_argument('--beta',type=float,required=True)
    p.add_argument('--liquid-mix',type=float,required=True)
    p.add_argument('--reason',required=True)
    args=p.parse_args()
    state_path=ROOT/'rsi/status.json'
    state=json.loads(state_path.read_text())
    if args.round!=state['rounds_completed']+1:raise ValueError('Round out of order or already finalized')
    candidate={'gain':args.gain,'beta':args.beta,'liquid_mix':args.liquid_mix}
    validate(candidate)
    before=dict(state['incumbent']);baseline={k:before[k] for k in candidate}
    pending={'round':args.round,'phase':'loading','incumbent':baseline,
             'candidate':candidate,'reason':args.reason,
             'proposal_selected_by':'assistant controller','started_unix':time.time()}
    atomic_json(ROOT/'rsi/pending.json',pending)
    model=load_port(ROOT,True);tok=tokenizer()
    apply_recipe(model,baseline)
    stored_previous_nll=before['development_nll']
    measured_baseline=development_score(model,tok)
    before['development_nll']=measured_baseline['mean_answer_nll']
    probe='What is 16 + 23? Reply only with the integer.'
    ids=prompt_ids(tok,probe)
    before_logits=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[0,-1].float().clone()
    q=('You are a small experimental language model. Your controller can edit these numeric weights: '
       'gain splits computation across two loop visits; beta activates inserted layers; liquid_mix '
       'blends seven-tap convolution weights. Current recipe: '+json.dumps(baseline)+
       '. Current development NLL: '+str(before['development_nll'])+
       '. Suggest one cautious change. Return a brief JSON object with gain, beta, liquid_mix.')
    suggestion_ids=prompt_ids(tok,q)
    suggestion=model.generate(input_ids=suggestion_ids,max_new_tokens=32,do_sample=False,
        use_cache=True,pad_token_id=tok.eos_token_id)
    raw=tok.decode(suggestion[0,suggestion_ids.shape[1]:],skip_special_tokens=True)
    pending.update(phase='proposal_recorded',student_raw_suggestion=raw)
    atomic_json(ROOT/'rsi/pending.json',pending)
    apply_recipe(model,candidate)
    after_logits=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[0,-1].float()
    score=development_score(model,tok)
    improvement=before['development_nll']-score['mean_answer_nll']
    accept=improvement>1e-4
    record={**pending,'phase':'complete','candidate_development':score,
            'incumbent_development_nll':before['development_nll'],
            'stored_previous_nll':stored_previous_nll,
            'remeasured_incumbent_development':measured_baseline,
            'improvement':improvement,'accepted':accept,
            'actual_probe_logit_change':(after_logits-before_logits).abs().max().item(),
            'backward_passes':0,'heldout_used':False,
            'finished_unix':time.time()}
    atomic_json(ROOT/f'rsi/round_{args.round:03d}.json',record)
    if accept:
        state['incumbent']={**candidate,'development_nll':score['mean_answer_nll']}
    else:
        state['incumbent']['development_nll']=before['development_nll']
    state.update(rounds_completed=args.round,status='checkpointed_between_rounds',
                 last_round_accepted=accept,last_round_file=f'rsi/round_{args.round:03d}.json')
    atomic_json(state_path,state)
    checkpoint={'base':state['base'],'revision':state['revision'],
        'recipe':state['incumbent'],
        'calibration_patch':'checkpoints/liquid_patch.pt',
        'patch_sha256':hashlib.sha256((ROOT/'checkpoints/liquid_patch.pt').read_bytes()).hexdigest(),
        'reconstruction':'download pinned Qwen, build 32-layer port, load_port(liquid=True), apply_recipe',
        'rounds_completed':args.round,'heldout_used_for_selection':False}
    atomic_json(ROOT/'checkpoints/incumbent.json',checkpoint)
    atomic_json(ROOT/'rsi/pending.json',{'phase':'none','last_completed_round':args.round})
    print(json.dumps({'round':args.round,'accepted':accept,'candidate_nll':score['mean_answer_nll'],
        'previous_nll':before['development_nll'],'incumbent':state['incumbent']},indent=2),flush=True)


if __name__=='__main__':main()
