"""Generation validation, frozen promotion, then one fresh final comparison."""
import argparse
import json
import resource

import torch
from common import *


def validate():
    raise RuntimeError('Use ci.py validate/freeze for the preregistered cycle2 gates')


def freeze():
    state=json.loads((HERE/'status.json').read_text())
    assert state['status']=='validation_complete'
    archive=json.loads((HERE/'archive.json').read_text())
    passed=[c for c in archive['candidates'] if c.get('passes_validation',False)]
    passed.sort(key=lambda c:(-c['validation']['exact_correct'],-c['development_generation']['exact_correct'],c['development']['mean_answer_nll']))
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


def heldout(variant):
    raise RuntimeError('Use ci.py heldout --variant MODEL --shard 0/1 for this cycle')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['validate','freeze','heldout'])
    p.add_argument('--variant',choices=['original','baseline','selected'])
    a=p.parse_args()
    if a.phase=='validate':validate()
    elif a.phase=='freeze':freeze()
    else:
        assert a.variant
        heldout(a.variant)
