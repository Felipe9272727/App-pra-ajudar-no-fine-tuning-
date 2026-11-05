"""Exact candidate freeze before the unopened, independent validation gate."""
from study008 import *

@torch.inference_mode()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['freeze','original','parent','candidate','select']);a=parser.parse_args()
    decision=json.loads((HERE/'trial_008.json').read_text());eligible=decision.get('eligible_for_validation',False)
    path=HERE/'validation_frozen.json'
    if a.phase=='freeze':
        assert not path.exists(),'Validation was already frozen; inspect it instead of overwriting'
        save(path.name,{'candidate_eligible':eligible,'parent_sha256':PARENT_HASH,
            'target_patch_sha256':e.cr.file_hash(HERE/'checkpoints/trial_008_target.pt'),
            'baseline_norms_sha256':e.cr.file_hash(HERE/'checkpoints/baseline_norms.pt'),
            'validation_source_sha256':e.cr.file_hash(Path(__file__)),
            'data_sha256':e.DATA_HASH,'validation_ids':[x['id'] for x in e.DATA['validation']],
            'previously_observed_validation_outputs':False})
        print('VALIDATION008_FROZEN',eligible,flush=True);return
    frozen=json.loads(path.read_text());assert frozen['candidate_eligible']==eligible
    assert frozen['validation_source_sha256']==e.cr.file_hash(Path(__file__))
    if a.phase=='select':
        result={'selected':'parent','checkpoint':'rsi100/checkpoints/best.pt',
            'checkpoint_sha256':PARENT_HASH,'patch':None,'checkpoint_promoted':False,
            'fresh_validation_consumed':eligible}
        if not eligible:result['reason']='Multi-tensor candidate failed development; validation remains unopened'
        else:
            reports={v:json.loads((HERE/f'validation_{v}.json').read_text()) for v in ['original','parent','candidate']}
            assert all(r['status']=='complete' for r in reports.values())
            old=reports['parent'];new=reports['candidate']
            passed=dominates(flatten(new['rows']),flatten(old['rows']))
            passed=passed and sum(r['all_passed'] for r in new['rows'])>sum(r['all_passed'] for r in old['rows'])
            passed=passed and all(not x or y for x,y in zip(old['control_bits'],new['control_bits']))
            passed=passed and new['anchor_nll']<=old['anchor_nll']+1e-6
            result['reason']='Independent task/case gain with retention' if passed else 'Independent gain/retention not confirmed'
            if passed:result.update(selected='trial008',checkpoint_promoted=True,
                patch='reasoning/multi008/checkpoints/trial_008_target.pt',
                patch_sha256=frozen['target_patch_sha256'],baseline_norms='reasoning/multi008/checkpoints/baseline_norms.pt',
                baseline_norms_sha256=frozen['baseline_norms_sha256'])
        save('selection.json',result);return
    assert eligible,'No eligible candidate; do not consume fresh validation'
    verify();assert frozen['data_sha256']==e.DATA_HASH
    model,meta=e.cr.load('original' if a.phase=='original' else 'baseline');tok=e.cr.tokenizer()
    if a.phase!='original':
        parent=e.read_checkpoint('best.pt');basepath=HERE/'checkpoints/baseline_norms.pt'
        assert e.cr.file_hash(basepath)==frozen['baseline_norms_sha256']
        baseline=torch.load(basepath,weights_only=True);patch=None
        if a.phase=='candidate':
            pp=HERE/'checkpoints/trial_008_target.pt';assert e.cr.file_hash(pp)==frozen['target_patch_sha256']
            patch=torch.load(pp,weights_only=True)
        meta['architecture']=apply(model,parent,baseline,patch)
    state(status='validation_'+a.phase,model_process_active=True)
    name=f'validation_{a.phase}.json';dest=HERE/name
    r=json.loads(dest.read_text()) if dest.exists() else {'rows':[],'controls':[],'status':'running','model':meta}
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
