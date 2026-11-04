"""Development selects a V3 head; a frozen new test compares actual generations."""
import argparse
import gc
import json
import resource
import time
import torch
from runtime import *


def make_experiment(model,tok,path):
    saved=torch.load(path,weights_only=True)
    assert saved['data_sha256']==DATA_HASH
    assert saved['codec_sha256']==file_hash(HERE/'codec.pt')
    assert saved['parent_patch_sha256']==file_hash(PARENT_PATCH)
    codec=load_codec(HERE/'codec.pt')
    embeds=torch.load(HERE/'query_embeddings.pt',weights_only=True)['bytes']
    return NCMExperiment(model,tok,codec,embeds,saved['heads'])


@torch.inference_mode()
def evaluate_rows(rows,variant,path,model,tok,experiment=None,patch_sha=None):
    result={'variant':variant,'data_sha256':DATA_HASH,'head_sha256':patch_sha,
        'status':'running','rows':[],'selection_uses_heldout':False,
        'protocol':{'cpu_threads':torch.get_num_threads(),'backbone':'BF16','routers':'FP32',
          'NCM_max_bytes':WIDTH if experiment else None,'baseline_max_new_tokens':8 if experiment is None else None,
          'decoding':'greedy codebook nearest-centre' if experiment else 'greedy autoregressive',
          'inference_tools':False,'thinking':False},
        'code_sha256':{p.name:file_hash(p) for p in [HERE/'runtime.py',HERE/'codec.py',HERE/'evaluate.py']}}
    if variant!='qwen_original':result['architecture']=architecture_check(model)
    if experiment:result['loaded_parameters']=sum(p.numel() for p in experiment.parameters())
    else:result['loaded_parameters']=sum(p.numel() for p in model.parameters())
    if path.exists():
        previous=json.loads(path.read_text())
        for k in ['variant','data_sha256','head_sha256','code_sha256']:
            assert previous[k]==result[k],('Cannot mix incompatible evaluations',k)
        assert [r['id'] for r in previous['rows']]==[r['id'] for r in rows[:len(previous['rows'])]]
        if previous['status']=='complete':return previous
        result['rows']=previous['rows']
    for row in rows[len(result['rows']):]:
        start=time.monotonic()
        if experiment:text,trace=experiment.generate(row['question'])
        else:
            ids=prompt_ids(tok,row['question'])
            generated=model.generate(input_ids=ids,max_new_tokens=8,do_sample=False,
                use_cache=True,pad_token_id=tok.eos_token_id)[0,ids.shape[1]:]
            text=tok.decode(generated,skip_special_tokens=True)
            trace={'new_tokens':len(generated),'hit_limit':len(generated)==8}
        exact,content=exact_grade(text,row);bc,bt=byte_accuracy(text,row['answer'])
        result['rows'].append({**row,'output':text,'exact_correct':exact,'content_correct':content,
            'byte_correct':bc,'byte_total':bt,'seconds':round(time.monotonic()-start,4),'trace':trace})
        atomic_json(path,result)
        print('ANSWER',variant,row['id'],repr(text),exact,content,flush=True)
    result.update(status='complete',total=len(rows),exact_correct=sum(r['exact_correct'] for r in result['rows']),
        content_correct=sum(r['content_correct'] for r in result['rows']),
        byte_accuracy=sum(r['byte_correct'] for r in result['rows'])/sum(r['byte_total'] for r in result['rows']),
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    atomic_json(path,result);return result


@torch.inference_mode()
def develop():
    assert not (HERE/'frozen.json').exists(),'Do not reopen selection after freezing'
    archive=json.loads((HERE/'archive.json').read_text())
    model,_=parent_model();tok=tokenizer()
    for head in archive['heads']:
        if head['status']=='development_complete':continue
        status(status='development_generation',evaluating=head['id'],model_process_active=True)
        exp=make_experiment(model,tok,ROOT/head['checkpoint'])
        result=evaluate_rows(DATA['development'],head['id'],HERE/f'development_{head["id"]}.json',
            model,tok,exp,head['sha256'])
        head.update(status='development_complete',exact_correct=result['exact_correct'],
            byte_accuracy=result['byte_accuracy'],total=result['total'])
        atomic_json(HERE/'archive.json',archive)
        del exp;gc.collect()
    best=max(archive['heads'],key=lambda h:(h['exact_correct'],h['byte_accuracy'],-h['ridge']))
    frozen={'status':'EXPERIMENTO_FROZEN','model_name':'liquid sense 0.8 b LOOP V3 NCM — EXPERIMENTO',
        'selected_head':best['id'],'checkpoint':best['checkpoint'],'checkpoint_sha256':best['sha256'],
        'codec':'v3_experiment/codec.pt','codec_sha256':file_hash(HERE/'codec.pt'),
        'query_embeddings_sha256':file_hash(HERE/'query_embeddings.pt'),
        'parent_patch':'lab_rsi/candidate_02.pt','parent_patch_sha256':file_hash(PARENT_PATCH),
        'liquid_patch_sha256':file_hash(ROOT/'checkpoints/liquid_patch.pt'),
        'data_sha256':DATA_HASH,'selected_by':'development exact answer accuracy then byte accuracy',
        'uses_heldout_for_selection':False,'frozen_unix':time.time(),
        'experiment_scope':DATA['protocol']['NCM_scope'],'backward_passes':0,
        'sensenova_and_liquid_required':True}
    atomic_json(HERE/'frozen.json',frozen)
    status(status='frozen_for_heldout',selected_head=best['id'],model_process_active=False,evaluating=None)
    print('FROZEN',json.dumps(frozen),flush=True)


@torch.inference_mode()
def heldout(variant):
    frozen=json.loads((HERE/'frozen.json').read_text())
    assert not frozen['uses_heldout_for_selection'] and frozen['data_sha256']==DATA_HASH
    path=HERE/f'heldout_{variant}.json'
    if path.exists() and json.loads(path.read_text())['status']=='complete':
        print('ALREADY_COMPLETE',variant,flush=True);return
    status(status='heldout_generation',evaluating=variant,model_process_active=True)
    tok=tokenizer();exp=None;sha=None
    if variant=='qwen_original':model=load_teacher()
    else:model,_=parent_model()
    if variant=='v3_ncm':
        checkpoint=ROOT/frozen['checkpoint'];assert file_hash(checkpoint)==frozen['checkpoint_sha256']
        exp=make_experiment(model,tok,checkpoint);sha=file_hash(checkpoint)
    result=evaluate_rows(DATA['heldout'],variant,path,model,tok,exp,sha)
    status(status='between_heldout_variants',evaluating=None,model_process_active=False)
    print('HELDOUT_COMPLETE',variant,result['exact_correct'],result['content_correct'],result['total'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['develop','heldout']);p.add_argument('--variant',choices=['qwen_original','v2_parent','v3_ncm'])
    a=p.parse_args()
    if a.phase=='develop':develop()
    else:
        assert a.variant;heldout(a.variant)
