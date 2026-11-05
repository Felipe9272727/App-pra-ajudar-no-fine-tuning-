"""Previously unopened RSI100 validation; frozen candidates, then no more edits."""
import argparse
import json
from runtime_helpers import *
from policy import flatten,dominates


@torch.inference_mode()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze-only',action='store_true');args=parser.parse_args()
    assert all((HERE/f'trial_{i:03d}.json').exists() for i in [3,4])
    candidates=[i for i in [3,4] if json.loads((HERE/f'trial_{i:03d}.json').read_text()).get('eligible_for_new_validation')]
    frozen_path=HERE/'validation_frozen.json'
    if not frozen_path.exists():
        assert args.freeze_only,'Freeze and commit candidates before any validation inference'
        save(frozen_path.name,{'candidate_trials':candidates,'parent_sha256':PARENT_HASH,
             'patches':{str(i):e.cr.file_hash(HERE/f'checkpoints/trial_{i:03d}_target.pt') for i in candidates},
             'data_sha256':e.DATA_HASH,'fresh_validation_ids':[x['id'] for x in e.DATA['validation']],
             'validation_previously_evaluated':False,'public_benchmarks_observed':False})
    frozen=json.loads(frozen_path.read_text());assert frozen['candidate_trials']==candidates
    if args.freeze_only:
        print('VALIDATION_FROZEN',candidates,flush=True);return
    if not candidates:
        save('selection.json',{'selected':'parent','checkpoint':'rsi100/checkpoints/best.pt',
            'checkpoint_sha256':PARENT_HASH,'patch':None,'checkpoint_promoted':False,
            'reason':'Neither authored edit passed development gates; keep unchanged hybrid'})
        print('NO_VALIDATION_CANDIDATES',flush=True);return
    model,tok,parent,_=load();results={}
    for name in ['parent']+[str(i) for i in candidates]:
        patch=None if name=='parent' else torch.load(HERE/f'checkpoints/trial_{int(name):03d}_target.pt',weights_only=True)
        apply(model,parent,patch)
        path=HERE/f'validation_{name}.json'
        report=json.loads(path.read_text()) if path.exists() else {'status':'running','rows':[],'controls':[]}
        seen={r['id'] for r in report['rows']}
        for task in e.DATA['validation']:
            if task['id'] not in seen:
                report['rows']+=e.coding(model,tok,[task]);save(path.name,report)
        seen={r['id'] for r in report['controls']}
        for row in e.DATA['controls']['val']:
            if row['id'] not in seen:
                report['controls']+=e.quality(model,tok,[row]);save(path.name,report)
        report['control_bits']=[x['correct'] for x in report['controls']]
        if 'anchor_nll' not in report:report['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
        report['status']='complete';save(path.name,report);results[name]=report
    base=results['parent'];eligible=[]
    for i in candidates:
        candidate=results[str(i)]
        ok=dominates(flatten(candidate['rows']),flatten(base['rows']))
        ok=ok and sum(x['all_passed'] for x in candidate['rows'])>sum(x['all_passed'] for x in base['rows'])
        ok=ok and all(not a or b for a,b in zip(base['control_bits'],candidate['control_bits']))
        ok=ok and candidate['anchor_nll']<=base['anchor_nll']+1e-6
        if ok:eligible.append(i)
    eligible.sort(key=lambda i:(-sum(x['all_passed'] for x in results[str(i)]['rows']),-sum(x['passed'] for x in results[str(i)]['rows']),i))
    selected=eligible[0] if eligible else None
    save('selection.json',{'selected':'trial_'+str(selected) if selected else 'parent',
        'checkpoint':'rsi100/checkpoints/best.pt','checkpoint_sha256':PARENT_HASH,
        'patch':f'reasoning/checkpoints/trial_{selected:03d}_target.pt' if selected else None,
        'patch_sha256':frozen['patches'][str(selected)] if selected else None,
        'checkpoint_promoted':bool(selected),'fresh_validation_passed':bool(selected),
        'reason':'Strict fresh task/case gain with controls and anchors retained' if selected else 'No candidate passed fresh transfer and retention gates'})
    apply(model,parent)
    print('VALIDATION_SELECTION',selected,flush=True)


if __name__=='__main__':main()
