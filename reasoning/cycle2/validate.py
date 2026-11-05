"""One unopened validation after all development decisions and exact-hash freeze."""
import argparse
import json
from run import *

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','original','parent','candidate','select']);a=p.parse_args()
    report=json.loads((HERE/'trial_006.json').read_text())
    eligible=report.get('eligible_for_new_validation',False)
    frozen_path=HERE/'validation_frozen.json'
    if a.phase=='freeze':
        assert not frozen_path.exists()
        save(frozen_path.name,{'candidate_trials':[6] if eligible else [],
            'parent_sha256':PARENT_HASH,'patch_sha256':report.get('patch_sha256'),
            'validation_ids':[x['id'] for x in e.DATA['validation']],
            'data_sha256':e.DATA_HASH,'previous_validation_outputs_observed':False,
            'protocol_sha256':e.cr.file_hash(HERE/'PROTOCOL.md'),
            'validation_source_sha256':e.cr.file_hash(Path(__file__))})
        return
    frozen=json.loads(frozen_path.read_text());assert frozen['candidate_trials']==([6] if eligible else [])
    assert e.cr.file_hash(Path(__file__))==frozen['validation_source_sha256']
    if a.phase=='select':
        choice={'checkpoint':'rsi100/checkpoints/best.pt','checkpoint_sha256':PARENT_HASH,
            'selected':'parent','patch':None,'checkpoint_promoted':False}
        if not eligible:choice['reason']='Hypothesis006 did not pass development; independent validation remains unopened'
        else:
            reports={k:json.loads((HERE/f'validation_{k}.json').read_text()) for k in ['original','parent','candidate']}
            assert all(r['status']=='complete' for r in reports.values())
            parent=reports['parent'];candidate=reports['candidate']
            passed=dominates(flatten(candidate['rows']),flatten(parent['rows']))
            passed=passed and sum(r['all_passed'] for r in candidate['rows'])>sum(r['all_passed'] for r in parent['rows'])
            passed=passed and all(not x or y for x,y in zip(parent['control_bits'],candidate['control_bits']))
            passed=passed and candidate['anchor_nll']<=parent['anchor_nll']+1e-6
            choice['reason']='Fresh task/case gain and retention' if passed else 'Failed independent gain/retention gates'
            if passed:choice.update(selected='trial006',patch='reasoning/cycle2/checkpoints/trial_006_target.pt',
                patch_sha256=frozen['patch_sha256'],checkpoint_promoted=True)
        save('selection.json',choice);return
    assert eligible,'No eligible candidate; do not consume new validation'
    verify();status(status='validation_'+a.phase,model_process_active=True)
    model,meta=e.cr.load('original' if a.phase=='original' else 'baseline');tok=e.cr.tokenizer()
    if a.phase!='original':
        parent=e.read_checkpoint('best.pt');patch=None
        if a.phase=='candidate':
            pp=HERE/'checkpoints/trial_006_target.pt';assert e.cr.file_hash(pp)==frozen['patch_sha256']
            patch=torch.load(pp,weights_only=True)
        meta['architecture']=apply(model,parent,patch)
    path=HERE/f'validation_{a.phase}.json'
    measured=json.loads(path.read_text()) if path.exists() else {'status':'running','rows':[],'controls':[],'model':meta}
    for task in e.DATA['validation']:
        if task['id'] not in {r['id'] for r in measured['rows']}:
            measured['rows']+=e.coding(model,tok,[task]);save(path.name,measured)
    for control in e.DATA['controls']['val']:
        if control['id'] not in {r['id'] for r in measured['controls']}:
            measured['controls']+=e.quality(model,tok,[control]);save(path.name,measured)
    measured['control_bits']=[r['correct'] for r in measured['controls']]
    measured['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
    measured['status']='complete';save(path.name,measured)
    status(status='validation_complete_'+a.phase,model_process_active=False)

if __name__=='__main__':
    with torch.inference_mode():main()
