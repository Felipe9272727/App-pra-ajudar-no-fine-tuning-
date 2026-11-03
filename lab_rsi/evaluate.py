"""Generation validation, frozen promotion, then one fresh final comparison."""
import argparse
import json
import resource

import torch
from common import *


@torch.inference_mode()
def validate():
    queue=json.loads((HERE/'validation_queue.json').read_text())['candidate_ids']
    archive=json.loads((HERE/'archive.json').read_text())
    state=json.loads((HERE/'status.json').read_text())
    assert state['status'] in ['awaiting_validation','validation_running','validation_complete']
    update_status(status='validation_running')
    model=load_hybrid();tok=tokenizer()
    base=generate_rows(model,tok,DATA['validation'],HERE/'validation_baseline.json',
        {'variant':'active_hybrid_baseline','recipe':RECIPE,'architecture':architecture_check(model)})
    for key in queue:
        candidate=next(c for c in archive['candidates'] if c['id']==key)
        patch=ROOT/candidate['patch']
        assert file_hash(patch)==candidate['patch_sha256']
        written=apply_edit(model,patch)
        result=generate_rows(model,tok,DATA['validation'],HERE/f'validation_{key}.json',
            {'variant':key,'patch_sha256':file_hash(patch),'recipe':RECIPE,'weight_write':written})
        candidate['validation']={k:result[k] for k in ['exact_correct','content_correct','total']}
        candidate['passes_validation']=(result['content_correct']>base['content_correct'] and
            result['exact_correct']>=base['exact_correct'])
        candidate['status']='validation_complete'
        atomic_json(HERE/'archive.json',archive)
    update_status(status='validation_complete')


def freeze():
    state=json.loads((HERE/'status.json').read_text())
    assert state['status']=='validation_complete'
    archive=json.loads((HERE/'archive.json').read_text())
    passed=[c for c in archive['candidates'] if c.get('passes_validation',False)]
    passed.sort(key=lambda c:(-c['validation']['content_correct'],c['development']['mean_answer_nll']))
    selected=passed[0] if passed else None
    frozen={'model_display_name':'liquid sense 0.8 b LOOP','data_sha256':DATA_HASH,
        'recipe':RECIPE,'candidate_id':selected['id'] if selected else None,
        'patch':selected['patch'] if selected else None,
        'patch_sha256':selected['patch_sha256'] if selected else None,
        'selection_used_heldout':False,'architecture_can_be_disabled':False,
        'reason':'Passed development, anchors and validation' if selected else
          'No new dense edit passed the preregistered gates; retain both active architecture components',
        'frozen_unix':time.time(),'protocol':DATA['protocol'],
        'liquid_patch_sha256':file_hash(ROOT/'checkpoints/liquid_patch.pt')}
    atomic_json(HERE/'frozen.json',frozen)
    update_status(status='frozen_for_final_test',selected_candidate=frozen['candidate_id'],
                  heldout_used_for_selection=False)
    print('FROZEN',json.dumps(frozen,ensure_ascii=False),flush=True)


@torch.inference_mode()
def heldout(variant):
    state=json.loads((HERE/'status.json').read_text())
    assert state['status'] in ['frozen_for_final_test','final_test_running','complete']
    frozen=json.loads((HERE/'frozen.json').read_text())
    assert frozen['data_sha256']==DATA_HASH and not frozen['selection_used_heldout']
    output=HERE/f'heldout_{variant}.json'
    if output.exists() and json.loads(output.read_text())['status']=='complete':
        print('ALREADY_COMPLETE',variant,flush=True);return
    update_status(status='final_test_running',evaluating_variant=variant)
    tok=tokenizer();metadata={'variant':variant,'recipe':None,'patch_sha256':None,
        'frozen_selection_sha256':file_hash(HERE/'frozen.json'),'selection_used_heldout':False}
    if variant=='original':model=load_teacher()
    else:
        model=load_hybrid();metadata['recipe']=RECIPE
        if variant=='selected' and frozen['patch']:
            path=ROOT/frozen['patch'];assert file_hash(path)==frozen['patch_sha256']
            metadata['weight_write']=apply_edit(model,path)
            metadata['patch_sha256']=file_hash(path)
        metadata['architecture']=architecture_check(model)
    ids=prompt_ids(tok,'Calculate 37 + 42. Reply only with the integer.')
    full=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits[:,-1].float()
    pre=model(input_ids=ids[:,:-1],use_cache=True,logits_to_keep=1)
    step=model(input_ids=ids[:,-1:],past_key_values=pre.past_key_values,
               use_cache=True,logits_to_keep=1).logits[:,-1].float()
    diagnostic={'max_abs_delta':float((full-step).abs().max()),
        'same_top_token':bool(full.argmax()==step.argmax())}
    assert diagnostic['same_top_token'] and diagnostic['max_abs_delta']<=.5,diagnostic
    metadata['cache_diagnostic']=diagnostic
    report=generate_rows(model,tok,DATA['heldout'],output,metadata)
    report['peak_rss_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    atomic_json(output,report)
    print('FINAL',variant,report['exact_correct'],report['content_correct'],report['total'],flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['validate','freeze','heldout'])
    p.add_argument('--variant',choices=['original','baseline','selected'])
    a=p.parse_args()
    if a.phase=='validate':validate()
    elif a.phase=='freeze':freeze()
    else:
        assert a.variant
        heldout(a.variant)
