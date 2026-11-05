"""Finite new research cycle; previous protocols/results are read-only."""
import argparse
import collections
import gc
import hashlib
import json
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import e,torch,load,apply,tasks,PARENT_HASH,tensor_checkpoint
from policy import dominates,flatten,accept_paired
sys.path.insert(0,str(ROOT/'benchmarks/reasoning_20261105'))
import evaluate as public

SCREEN=['prefix_sums','rotate_right','longest_run','sum_abs','palindrome','binary_search']
DIAG_IDS=['gsm8k:914','gsm8k:501','lcb:abc387_a']

def save(name,value):e.cr.atomic_json(HERE/name,value)

def status(**kw):
    old=json.loads((HERE/'status.json').read_text());old.update(kw,updated_unix=time.time());save('status.json',old)

def freeze():
    paths=['reasoning/cycle2/PROTOCOL.md','reasoning/cycle2/run.py',
           'reasoning/traces.pt','reasoning/trial_004.json',
           'rsi100/data.json','rsi100/checkpoints/best.pt',
           'benchmarks/reasoning_20261105/prompts.json',
           'benchmarks/reasoning_20261105/oracles.json']
    save('frozen.json',{'files':{p:e.cr.file_hash(ROOT/p) for p in paths},
        'diagnostic_ids':DIAG_IDS,'thinking_modes':[False,True],'max_tokens':512,
        'sampling':False,'new_hypotheses':[6],'final_validation_observed':False})

def verify():
    for p,h in json.loads((HERE/'frozen.json').read_text())['files'].items():
        assert e.cr.file_hash(ROOT/p)==h,p

@torch.inference_mode()
def edit():
    verify();path=HERE/'trial_006.json';assert not path.exists(),'Inspect existing outcome'
    status(status='constructing_006',model_process_active=True)
    model,tok,parent,meta=load()
    traces=torch.load(ROOT/'reasoning/traces.pt',weights_only=True)
    old=json.loads((ROOT/'reasoning/trial_004.json').read_text())['metadata']
    index=old['target_index'];bad=old['bad_token'];own=traces['rotate_right']
    assert int(own['token_ids'][index])==bad
    h=own['states'][index].float()
    code_p=torch.cat([own['states'][:index]]+[traces[k]['states'] for k in ['sum_abs','palindrome','binary_search']])
    anchor_states=[]
    def capture(module,inputs):anchor_states.append(inputs[0].detach().float().reshape(-1,inputs[0].shape[-1]).clone())
    handle=model.model.language_model.layers[31].mlp.down_proj.register_forward_pre_hook(capture)
    try:
        for text in e.DATA['anchors']:
            ids=tok(text,return_tensors='pt',add_special_tokens=False)['input_ids']
            model(input_ids=ids,use_cache=False,logits_to_keep=1)
    finally:handle.remove()
    p=torch.cat([code_p]+anchor_states)
    _,s,vh=torch.linalg.svd(p,full_matrices=False)
    basis=vh[s>s[0]*1e-5]
    residual=h-basis.T@(basis@h)
    ratio=float(residual.norm()/h.norm())
    report={'trial':6,'stage':'constructed','parent_sha256':PARENT_HASH,
        'metadata':{'edited_tensor':'model.language_model.layers.31.mlp.down_proj.weight',
          'bad_token':bad,'bad_piece':tok.decode([bad]),'target_index':index,
          'protected_code_states':len(code_p),'protected_anchor_states':sum(len(x) for x in anchor_states),
          'preservation_rank':len(basis),'svd_relative_cutoff':1e-5,'residual_ratio':ratio,
          'dose':.006,'correct_replacement_or_solution_supplied':False},
        'checkpoint_promoted':False,'backward_passes':0,'screens':{}}
    save(path.name,report)
    if ratio<.05:
        report.update(stage='aborted_unstable_direction',eligible_for_new_validation=False)
        save(path.name,report);status(status=report['stage'],model_process_active=False);return
    v=residual/residual.norm()
    u=model.get_output_embeddings().weight[bad].detach().float().clone();u/=u.norm()
    w=parent['dense_weight'].float();ideal=-.006*w.norm()*torch.outer(u,v)
    written=(w+ideal).to(parent['dense_weight'].dtype);delta=written.float()-w
    def effect(d,x):return (x@d.T).norm(dim=1)
    report['metadata'].update(changed_values=int((written!=parent['dense_weight']).sum()),
        actual_relative_norm=float(delta.norm()/w.norm()),
        normalized_preservation_projection_max=float((p@v/p.norm(dim=1)).abs().max()),
        target_direct_bad_logit_delta=float(u@(delta@h)),
        ideal_protected_output_norm_max=float(effect(ideal,p).max()),
        rounded_protected_output_norm_max=float(effect(delta,p).max()),
        rounded_protected_output_norm_mean=float(effect(delta,p).mean()),
        rounding_error_relative_to_ideal=float((delta-ideal).norm()/ideal.norm()))
    top=delta.abs().flatten().topk(20).indices
    report['metadata']['largest_actual_changes']=[{'row':int(i//w.shape[1]),'column':int(i%w.shape[1]),
        'before':float(w.flatten()[i]),'after':float(written.flatten()[i])} for i in top]
    patch={'parent_sha256':PARENT_HASH,'hypothesis':6,'dense_weight':written}
    tensor_checkpoint(patch,HERE/'checkpoints/trial_006_target.pt')
    tensor_checkpoint({'input_direction':v,'negative_output_direction':u,
        'preservation_states':p,'target_state':h,'singular_values':s},HERE/'directions_006.pt')
    report['patch_sha256']=e.cr.file_hash(HERE/'checkpoints/trial_006_target.pt');save(path.name,report)
    baseline={r['id']:r for r in json.loads((ROOT/'reasoning/diagnostic.json').read_text())['rows']}
    try:
        report['architecture']=apply(model,parent,patch)
        report['screens']['target']=e.coding(model,tok,tasks(SCREEN));save(path.name,report)
        if not dominates(flatten(report['screens']['target']),flatten([baseline[x] for x in SCREEN])):
            report.update(stage='rejected_on_screen',eligible_for_new_validation=False,
                reason='No strict case gain with complete retention of screen')
        else:
            results={}
            for name,overlay in [('parent',None),('target',patch)]:
                apply(model,parent,overlay)
                full={'rows':[],'controls':[],'status':'running'}
                dest=f'trial_006_{name}_full.json'
                for task in e.DATA['search']+e.DATA['guard']:
                    full['rows']+=e.coding(model,tok,[task]);save(dest,full)
                for row in e.DATA['search_controls']:
                    full['controls']+=e.quality(model,tok,[row]);save(dest,full)
                full['control_bits']=[r['correct'] for r in full['controls']]
                full['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
                full['status']='complete';save(dest,full);results[name]=full
            accepted,reason=accept_paired(results['target'],results['parent'],
                json.loads((ROOT/'rsi100/best_metrics.json').read_text()))
            report.update(stage='eligible_for_new_validation' if accepted else 'rejected_full_gates',
                eligible_for_new_validation=accepted,reason=reason)
    finally:apply(model,parent)
    save(path.name,report);status(status=report['stage'],model_process_active=False)
    print('TRIAL006',report['stage'],report.get('reason'),flush=True)

@torch.inference_mode()
def diagnostic(variant):
    verify();path=HERE/f'thinking_{variant}.json'
    report=json.loads(path.read_text()) if path.exists() else {'variant':variant,'rows':[],
        'status':'running','purpose':'observed diagnostic; not independent weight validation',
        'matched_protocol':{'greedy':True,'thinking_modes':[False,True],'max_new_tokens':512,
            'threads':4,'BF16':True,'cache':True,'seed':0,'reference_answers_in_prompt':False}}
    if report['status']=='complete':return
    status(status='thinking_diagnostic_'+variant,model_process_active=True)
    model,meta=e.cr.load('original' if variant=='original' else 'baseline');tok=e.cr.tokenizer()
    if variant=='liquid':
        parent=e.read_checkpoint('best.pt');meta['architecture']=apply(model,parent)
    report['model']=meta
    bank={x['id']:x for x in json.loads((ROOT/'benchmarks/reasoning_20261105/prompts.json').read_text())}
    oracles=json.loads((ROOT/'benchmarks/reasoning_20261105/oracles.json').read_text())
    seen={(r['id'],r['thinking']) for r in report['rows']}
    traces={};trace_path=HERE/'thinking_trace.pt'
    if trace_path.exists():traces=torch.load(trace_path,weights_only=True)
    for thinking in [False,True]:
        for key in DIAG_IDS:
            if (key,thinking) in seen:continue
            task=bank[key];ids=e.cr.prompt(tok,task['prompt'],thinking=thinking)
            early=[];tail=collections.deque(maxlen=16);norms=[];hook=None
            if variant=='liquid':
                def capture(module,inputs):
                    x=inputs[0][0,-1].detach().float()
                    i=len(norms);norms.append(float(x.norm()))
                    item=(i,x.to(torch.float16).clone())
                    if i<64:early.append(item)
                    tail.append(item)
                hook=model.model.language_model.layers[31].mlp.down_proj.register_forward_pre_hook(capture)
            started=time.monotonic();torch.manual_seed(0)
            try:
                output=model.generate(input_ids=ids,max_new_tokens=512,use_cache=True,
                    do_sample=False,pad_token_id=tok.eos_token_id)[0,ids.shape[1]:]
            finally:
                if hook:hook.remove()
            text=tok.decode(output,skip_special_tokens=True)
            scored=public.grade(task,text,oracles[key])
            generated={'id':key,'thinking':thinking,'output':text,'new_tokens':len(output),
                'hit_limit':len(output)==512,'seconds':time.monotonic()-started,
                'thinking_closed':('</think>' in text) if thinking else None,
                'prompt_sha256':hashlib.sha256(task['prompt'].encode()).hexdigest(),
                'template_tail':tok.decode(ids[0,-24:],skip_special_tokens=False),**scored}
            report['rows'].append(generated);save(path.name,report)
            if variant=='liquid':
                kept=dict(early+list(tail));traces[f'{key}:{thinking}']={
                    'token_ids':output.cpu(),'state_indices':torch.tensor(list(kept)),
                    'states':torch.stack(list(kept.values())),'all_input_norms':torch.tensor(norms),
                    'state_storage':'FP16 first64 and last16 actual cached decoding states'}
                tensor_checkpoint(traces,trace_path)
            print('THINK_DIAG',variant,key,thinking,scored['passed'],scored['total'],len(output),flush=True)
    report['status']='complete';save(path.name,report)
    status(status='diagnostic_complete_'+variant,model_process_active=False)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['freeze','edit','original','liquid'])
    args=parser.parse_args()
    if args.phase=='freeze':freeze()
    elif args.phase=='edit':edit()
    else:diagnostic(args.phase)
