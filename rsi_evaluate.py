"""Frozen held-out comparison; this script never edits the promotion state."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import torch

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'v2_adaptation'))
from experiment import DATA,DATA_HASH,load_teacher,prompt_ids,tokenizer,grade
from native_runtime import load_port
from rsi_cycle import apply_recipe,atomic_json

torch.set_grad_enabled(False)
torch.set_num_threads(8)


@torch.inference_mode()
def main():
    p=argparse.ArgumentParser();p.add_argument('variant',choices=['original','incumbent','liquid'])
    args=p.parse_args()
    state=json.loads((ROOT/'rsi/status.json').read_text())
    if state['rounds_completed']<3:raise ValueError('Finish the three development rounds before held-out evaluation.')
    if state['status'] not in ['frozen_for_evaluation','pilot_complete']:
        raise ValueError('The assistant controller must freeze the selected recipe before held-out evaluation.')
    tok=tokenizer()
    if args.variant=='original':
        recipe=None;model=load_teacher()
    else:
        if args.variant=='incumbent':
            recipe={k:state['incumbent'][k] for k in ['gain','beta','liquid_mix']}
        else:
            recipe={'gain':0.05,'beta':0.,'liquid_mix':1.}
        model=load_port(ROOT,True);apply_recipe(model,recipe)
    # Cache consistency includes each actual windowed operator on short prompts.
    ids=prompt_ids(tok,'What is 14 + 22? Reply only with the integer.')
    full=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[:,-1].float()
    pre=model(input_ids=ids[:,:-1],use_cache=True,logits_to_keep=1)
    step=model(input_ids=ids[:,-1:],past_key_values=pre.past_key_values,
               use_cache=True,logits_to_keep=1).logits[:,-1].float()
    diagnostic={'max_abs_delta':(full-step).abs().max().item(),
                'same_top_token':full.argmax().item()==step.argmax().item()}
    assert diagnostic['same_top_token'] and diagnostic['max_abs_delta']<=0.5,diagnostic
    output=ROOT/'evaluation'/f'{args.variant}.json'
    report={'variant':args.variant,'recipe':recipe,'data_sha256':DATA_HASH,
            'protocol':{'mode':'non-thinking','decoding':'greedy','max_new_tokens':12,
                'device':'cpu','threads':8,'backbone':'BF16','routers':'FP32','use_cache':True},
            'cache_check':diagnostic,'rows':[],'status':'running',
            'selection_used_test':False,'rounds_before_evaluation':state['rounds_completed']}
    for item in DATA['heldout']:
        ids=prompt_ids(tok,item['question']);started=time.monotonic()
        result=model.generate(input_ids=ids,max_new_tokens=12,do_sample=False,
            use_cache=True,pad_token_id=tok.eos_token_id)
        new=result[0,ids.shape[1]:];text=tok.decode(new,skip_special_tokens=True)
        row={**item,'output':text,'correct':grade(text,item),
             'new_tokens':len(new),'hit_limit':len(new)==12,
             'seconds':round(time.monotonic()-started,4)}
        report['rows'].append(row);atomic_json(output,report)
        print(args.variant,item['id'],repr(text),row['correct'],flush=True)
    report.update(status='complete',correct=sum(r['correct'] for r in report['rows']),
        total=len(report['rows']),peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    atomic_json(output,report)
    print('COMPLETE',args.variant,report['correct'],report['total'],flush=True)


if __name__=='__main__':main()
