"""Matched greedy inference and sandbox scoring; no teaching targets in prompts."""
from core import *
from local_cpu.sandbox import evaluate as judge
import ast


def verify_stage(name):
    verify_frozen()
    audit=read('frozen_'+name+'.json')
    assert all(verify_source(p,h) for p,h in audit.items()),'Stage source freeze mismatch'


def prefix(tok,row,thinking=False,messages=None,tools=None):
    kw={'tools':tools} if tools else {}
    return tok.apply_chat_template(messages or [{'role':'user','content':row['prompt']}],
        tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=thinking,**kw)


@torch.inference_mode()
def generate(model,tok,row,thinking,budget,bypass=False,messages=None,tools=None):
    ids=torch.tensor([prefix(tok,row,thinking,messages,tools)],dtype=torch.long)
    first=[None];states=[];hook=None
    if bypass:
        block=model.model.language_model.layers[27]
        def capture(m,args,out):
            if m._last_native_visit==0:first[0]=out.detach().clone()
            elif m._last_native_visit==1:
                assert first[0] is not None
                a=first[0][0,-1].float().flatten();b=out[0,-1].float().flatten()
                states.append({'relative_L2':float((b-a).norm()/a.norm().clamp_min(1e-12)),
                    'cosine':float(F.cosine_similarity(a,b,dim=0))})
                return first[0]
        hook=block.register_forward_hook(capture)
    start=time.monotonic()
    try:
        out=model.generate(input_ids=ids,max_new_tokens=budget,do_sample=False,use_cache=True,
            pad_token_id=tok.eos_token_id,eos_token_id=read('config.json')['eos_ids'])[0,ids.shape[1]:]
    finally:
        if hook:hook.remove()
    tokens=out.tolist();raw=tok.decode(tokens,skip_special_tokens=True)
    ended=bool(tokens) and tokens[-1] in read('config.json')['eos_ids']
    final=delivered(raw,thinking)
    return {'ids':tokens,'raw':raw,'delivered':final,'tokens':len(tokens),'ended_eos':ended,
        'hit_limit':len(tokens)==budget and not ended,'thinking':thinking,
        'thinking_closed':not thinking or '</think>' in raw,
        'seconds_descriptive_only':time.monotonic()-start,
        'repeated_8gram_fraction':repeat_fraction(tokens),
        'second_exit_replaced_by_first':bypass,'replacement_diagnostics':states}


def repeat_fraction(tokens):
    grams=[tuple(tokens[i:i+8]) for i in range(max(0,len(tokens)-7))]
    return (len(grams)-len(set(grams)))/len(grams) if grams else 0.


def score(out,row,kind):
    if kind=='code':
        out.update(judge(out['delivered'],row))
        if 'case_passed' not in out:
            assert out['passed']==0
            out['case_passed']=[False]*out['total']
            out['case_bits_derived_from_preexecution_rejection']=True
        try:ast.parse(out['code']);out['syntax_valid']=True
        except SyntaxError:out['syntax_valid']=False
    else:out['correct']=bool(out['thinking_closed'] and grade_general(out['delivered'],row))
    return out


def run_variant(variant,split='validation',bypass=False,diagnostic_only=False):
    verify_stage('evaluation')
    name=f'reports/{split}_{variant}'+('_bypass' if bypass else '')+'.json'
    path=H/name
    report=read(name) if path.exists() else {'variant':variant,'split':split,'rows':[],
        'protocol':{'sampling':False,'threads':4,'eos_ids':read('config.json')['eos_ids'],
            'reference_or_cases_in_inputs':False,'same_native_BF16_cache':True,
            'bypass_all56_executions_retained':bypass}}
    if report.get('status')=='complete':print('SKIP028_COMPLETE',name,flush=True);return report
    model,tok,meta=load_variant(variant);report['metadata']=meta
    cfg=read('config.json')
    code=read('data/'+('validation' if diagnostic_only else split)+'_code.json')
    general=read('data/'+split+'_general.json') if not diagnostic_only else []
    for thinking in ([True] if diagnostic_only else [False,True]):
        jobs=[('code',row) for row in (code[:2] if diagnostic_only else code)]
        jobs += [('general',row) for row in (general[:4] if thinking else general)]
        for kind,row in jobs:
            key=(kind,row['id'],thinking)
            if key in {(x['kind'],x['id'],x['thinking']) for x in report['rows']}:continue
            budget=cfg['thinking_budget_total'] if thinking else cfg['code_budget' if kind=='code' else 'general_budget']
            out=score(generate(model,tok,row,thinking,budget,bypass=bypass),row,kind)
            out.update(id=row['id'],kind=kind,budget=budget);report['rows'].append(out);save(name,report)
            print('EVAL028',split,variant,thinking,row['id'],out.get('passed',out.get('correct')),out['tokens'],flush=True)
    report['status']='complete';report['summary']=summarize(report);save(name,report)
    del model;gc.collect();return report


def summarize(report):
    result={}
    for thinking in [False,True]:
        rows=[r for r in report['rows'] if r['thinking']==thinking]
        codes=[r for r in rows if r['kind']=='code'];gens=[r for r in rows if r['kind']=='general']
        result[str(thinking)]={'code_tasks':sum(r['all_passed'] for r in codes),'code_total':len(codes),
            'cases':sum(r['passed'] for r in codes),'case_total':sum(r['total'] for r in codes),
            'general_correct':sum(r['correct'] for r in gens),'general_total':len(gens),
            'tokens':sum(r['tokens'] for r in rows),'unfinished_thinking':sum(not r['thinking_closed'] for r in rows),
            'truncated':sum(r['hit_limit'] for r in rows)}
    return result
