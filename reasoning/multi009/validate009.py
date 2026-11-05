"""Unopened validation after exact four-matrix candidate freeze."""
from study009 import *

@torch.inference_mode()
def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','original','parent','candidate','select']);a=p.parse_args()
    decision=json.loads((HERE/'trial_009.json').read_text());eligible=decision.get('eligible_for_validation',False)
    frozen_path=HERE/'validation_frozen.json'
    if a.phase=='freeze':
        assert not frozen_path.exists()
        manifest=HERE/'patch_target.json'
        save(frozen_path.name,{'eligible':eligible,'parent_sha256':PARENT_HASH,
            'manifest_sha256':e.cr.file_hash(manifest) if manifest.exists() else None,
            'baseline_hashes_sha256':e.cr.file_hash(HERE/'baseline_hashes.json'),
            'validation_source_sha256':e.cr.file_hash(Path(__file__)),
            'data_sha256':e.DATA_HASH,'validation_ids':[x['id'] for x in e.DATA['validation']],
            'validation_outputs_previously_observed':False});return
    frozen=json.loads(frozen_path.read_text());assert frozen['eligible']==eligible
    assert frozen['validation_source_sha256']==e.cr.file_hash(Path(__file__))
    if a.phase=='select':
        choice={'selected':'parent','checkpoint':'rsi100/checkpoints/best.pt','checkpoint_sha256':PARENT_HASH,
            'patch_manifest':None,'checkpoint_promoted':False,'fresh_validation_consumed':eligible}
        if not eligible:choice['reason']='Vector-transport candidate did not pass development; validation unopened'
        else:
            reports={k:json.loads((HERE/f'validation_{k}.json').read_text()) for k in ['original','parent','candidate']}
            assert all(r['status']=='complete' for r in reports.values())
            old=reports['parent'];new=reports['candidate']
            passed=dominates(flatten(new['rows']),flatten(old['rows']))
            passed=passed and sum(r['all_passed'] for r in new['rows'])>sum(r['all_passed'] for r in old['rows'])
            passed=passed and all(not x or y for x,y in zip(old['control_bits'],new['control_bits']))
            passed=passed and new['anchor_nll']<=old['anchor_nll']+1e-6
            choice['reason']='Independent gain and retention confirmed' if passed else 'Independent gain/retention not confirmed'
            if passed:choice.update(selected='trial009',checkpoint_promoted=True,
                patch_manifest='reasoning/multi009/patch_target.json',manifest_sha256=frozen['manifest_sha256'])
        save('selection.json',choice);return
    assert eligible,'No eligible candidate; preserve the unused validation'
    verify();assert frozen['data_sha256']==e.DATA_HASH
    assert frozen['baseline_hashes_sha256']==e.cr.file_hash(HERE/'baseline_hashes.json')
    model,meta=e.cr.load('original' if a.phase=='original' else 'baseline');tok=e.cr.tokenizer()
    if a.phase!='original':
        parent=e.read_checkpoint('best.pt');apply_parent(model,parent);baseline=snapshot(model)
        expected=json.loads((HERE/'baseline_hashes.json').read_text())
        assert all(tensor_hash(w)==expected[k] for k,w in baseline.items())
        patch=None
        if a.phase=='candidate':
            assert e.cr.file_hash(HERE/'patch_target.json')==frozen['manifest_sha256'];patch=patch_weights('target')
        meta['architecture']=apply(model,parent,baseline,patch)
    state(status='validation_'+a.phase,model_process_active=True)
    name=f'validation_{a.phase}.json';path=HERE/name
    r=json.loads(path.read_text()) if path.exists() else {'status':'running','rows':[],'controls':[],'model':meta}
    for task in e.DATA['validation']:
        if task['id'] not in {x['id'] for x in r['rows']}:
            r['rows']+=e.coding(model,tok,[task]);save(name,r)
    for row in e.DATA['controls']['val']:
        if row['id'] not in {x['id'] for x in r['controls']}:
            r['controls']+=e.quality(model,tok,[row]);save(name,r)
    r['control_bits']=[x['correct'] for x in r['controls']]
    r['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
    r['status']='complete';save(name,r);state(status='validation_complete_'+a.phase,model_process_active=False)

if __name__=='__main__':main()
