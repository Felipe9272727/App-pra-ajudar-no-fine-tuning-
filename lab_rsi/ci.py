"""Bounded GitHub Actions research evaluation; no background training service."""
import argparse
import gc
import json
import os
import platform
import resource
import shutil
import sys
from pathlib import Path

from common import *
from ci_merge import merge_shards

CI=ROOT/'ci_output'


def runtime():
    import transformers
    return {'run_id':os.environ.get('GITHUB_RUN_ID'),'source_commit':os.environ.get('GITHUB_SHA'),
        'runner':os.environ.get('RUNNER_NAME'),'platform':platform.platform(),
        'python':platform.python_version(),
        'torch':torch.__version__,'transformers':transformers.__version__,
        'cpu_threads':CPU_THREADS,'data_sha256':DATA_HASH,'architecture_required':RECIPE}


def export_stage(stage,files):
    dest=CI/stage
    for relative in files:
        path=ROOT/relative
        if path.exists():
            target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target)
    atomic_json(dest/'lab_rsi'/f'ci_{stage}_runtime.json',runtime())


def develop():
    import fit
    state=json.loads((HERE/'status.json').read_text())
    if state.get('final_test_evaluated') or (HERE/'frozen.json').exists():
        raise RuntimeError('This test was already frozen/observed. Start a fresh pilot instead of reselecting on it.')
    update_status(status='github_development',execution=runtime(),
        model_process_active=True,process_continues_in_background=False)
    try:fit.develop()
    finally:
        update_status(model_process_active=False)
        export_stage('development',[str(p.relative_to(ROOT)) for p in HERE.glob('*.json')
            if p.name not in ['data.json','ci_run_request.json']] +
            [str(p.relative_to(ROOT)) for p in HERE.glob('candidate_*.pt')])


def validation_matrix():
    queue=json.loads((HERE/'validation_queue.json').read_text())['candidate_ids']
    assert all(x in {f'candidate_{i:02d}' for i in range(1,4)} for x in queue)
    return ['baseline']+queue


@torch.inference_mode()
def validate_variant(variant):
    assert variant in validation_matrix()
    model=load_hybrid();tok=tokenizer()
    meta={'variant':'active_hybrid_baseline','recipe':RECIPE,'architecture':architecture_check(model),
          'execution':runtime()}
    name='validation_baseline.json'
    if variant!='baseline':
        archive=json.loads((HERE/'archive.json').read_text())
        c=next(c for c in archive['candidates'] if c['id']==variant)
        path=ROOT/c['patch'];assert file_hash(path)==c['patch_sha256']
        meta.update(variant=variant,patch_sha256=file_hash(path),weight_write=apply_edit(model,path))
        name=f'validation_{variant}.json'
    try:generate_rows(model,tok,DATA['validation'],HERE/name,meta)
    finally:export_stage(f'validation-{variant}',[f'lab_rsi/{name}'])


def freeze():
    import evaluate
    from protocol import controls_correct,validation_passes
    from publish_progress import publish
    archive=json.loads((HERE/'archive.json').read_text())
    base=json.loads((HERE/'validation_baseline.json').read_text())
    assert base['status']=='complete' and base['data_sha256']==DATA_HASH
    for key in validation_matrix()[1:]:
        c=next(c for c in archive['candidates'] if c['id']==key)
        v=json.loads((HERE/f'validation_{key}.json').read_text())
        assert v['status']=='complete' and v['data_sha256']==DATA_HASH
        assert v['patch_sha256']==c['patch_sha256']
        assert v['inference_code_sha256']==base['inference_code_sha256']
        assert v['protocol']==base['protocol']
        c.update(status='validation_complete',validation={**{k:v[k] for k in ['exact_correct','content_correct','total']},'controls_exact':controls_correct(v),'baseline_controls_exact':controls_correct(base)},
            passes_validation=c['validation_eligible'] and validation_passes(v,base))
    atomic_json(HERE/'archive.json',archive)
    update_status(status='validation_complete',execution=runtime(),model_process_active=False)
    evaluate.freeze()
    publish('freeze selection before final test')
    frozen=json.loads((HERE/'frozen.json').read_text())
    export_stage('frozen',['lab_rsi/archive.json','lab_rsi/status.json','lab_rsi/frozen.json']+([frozen['patch']] if frozen['patch'] else []))


@torch.inference_mode()
def heldout(variant,shard,shards):
    assert shards==2 and 0<=shard<shards
    frozen=json.loads((HERE/'frozen.json').read_text())
    assert frozen['data_sha256']==DATA_HASH and not frozen['selection_used_heldout']
    assert variant in ['original','baseline']+(['selected'] if frozen['patch'] else [])
    metadata={'variant':variant,'recipe':None,'patch_sha256':None,'shard':shard,'shards':shards,
        'execution':runtime(),'frozen_selection_sha256':file_hash(HERE/'frozen.json'),
        'selection_used_heldout':False}
    tok=tokenizer()
    if variant=='original':model=load_teacher()
    else:
        model=load_hybrid();metadata.update(recipe=RECIPE,architecture=architecture_check(model))
        if variant=='selected':
            path=ROOT/frozen['patch'];assert file_hash(path)==frozen['patch_sha256']
            metadata.update(patch_sha256=file_hash(path),weight_write=apply_edit(model,path))
    torch.set_num_threads(CPU_THREADS)
    metadata['loaded_parameters']=sum(p.numel() for p in model.parameters())
    ids=prompt_ids(tok,'Calculate 37 + 42. Reply only with the integer.')
    full=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[:,-1].float()
    pre=model(input_ids=ids[:,:-1],use_cache=True,logits_to_keep=1)
    step=model(input_ids=ids[:,-1:],past_key_values=pre.past_key_values,
        use_cache=True,logits_to_keep=1).logits[:,-1].float()
    check={'max_abs_delta':float((full-step).abs().max()),'same_top_token':bool(full.argmax()==step.argmax())}
    assert check['same_top_token'] and check['max_abs_delta']<=.5,check
    metadata['cache_diagnostic']=check
    rows=DATA['heldout'][shard::shards]
    name=f'heldout_{variant}_shard_{shard}.json'
    try:
        result=generate_rows(model,tok,rows,HERE/name,metadata)
        result['peak_rss_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
        atomic_json(HERE/name,result)
    finally:export_stage(f'heldout-{variant}-{shard}',[f'lab_rsi/{name}'])


def aggregate():
    import summarize
    frozen=json.loads((HERE/'frozen.json').read_text())
    ids=[r['id'] for r in DATA['heldout']]
    for variant in ['original','baseline']+(['selected'] if frozen['patch'] else []):
        parts=[json.loads((HERE/f'heldout_{variant}_shard_{i}.json').read_text()) for i in range(2)]
        merged=merge_shards(parts,ids)
        assert merged['data_sha256']==DATA_HASH
        assert merged['frozen_selection_sha256']==file_hash(HERE/'frozen.json')
        atomic_json(HERE/f'heldout_{variant}.json',merged)
    summarize.main()
    update_status(execution=runtime(),model_process_active=False,
        completion_note='Bounded GitHub Actions pilot finished; no permanent training loop')
    files=['LAB_REPORT.md','checkpoints/liquid_sense_loop.json']
    files += [str(p.relative_to(ROOT)) for p in HERE.glob('*.json') if not p.name.startswith('heldout_') or '_shard_' not in p.name]
    export_stage('final',files)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['develop','validation-matrix','validate','freeze','final-matrix','heldout','aggregate'])
    p.add_argument('--variant');p.add_argument('--shard',type=int);a=p.parse_args()
    if a.phase=='develop':develop()
    elif a.phase=='validation-matrix':print(json.dumps(validation_matrix()))
    elif a.phase=='validate':validate_variant(a.variant)
    elif a.phase=='freeze':freeze()
    elif a.phase=='final-matrix':
        f=json.loads((HERE/'frozen.json').read_text());print(json.dumps(['original','baseline']+(['selected'] if f['patch'] else [])))
    elif a.phase=='heldout':heldout(a.variant,a.shard,2)
    else:aggregate()
