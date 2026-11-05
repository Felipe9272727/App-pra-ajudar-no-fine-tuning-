"""Authored selective third-visit hypothesis; no changes to dense matrices."""
import json
from runtime_helpers import *
from trial import SCREEN,full
from policy import flatten,dominates,accept_paired


@torch.inference_mode()
def main():
    assert not (HERE/'trial_005.json').exists(),'Inspect saved trial before resuming'
    assert json.loads((HERE/'trial_003.json').read_text())['stage']=='rejected_on_screen'
    diag=json.loads((HERE/'diagnostic.json').read_text())
    model,tok,parent,_=load();patches={}
    for kind,key in [('target','target_layers'),('layer_control','control_layers')]:
        selected=set(diag[key])
        gains={}
        for i in range(4,28):
            third=.025 if i in selected else .000001
            gains[str(i)]=torch.tensor([1-.05-third,.05,third],dtype=torch.float32)
        patch={'parent_sha256':PARENT_HASH,'hypothesis':5,'kind':kind,'passes':3,'layer_visit_gains':gains}
        tensor_checkpoint(patch,HERE/f'checkpoints/trial_005_{kind}.pt');patches[kind]=patch
    report={'trial':5,'stage':'constructed','parent_sha256':PARENT_HASH,'screens':{},
        'metadata':{'passes':3,'layer_executions':80,'target_layers':diag['target_layers'],'control_layers':diag['control_layers']},
        'backward_passes':0,'checkpoint_promoted':False,'fresh_benchmark_used':False}
    save('trial_005.json',report)
    base={r['id']:r for r in diag['rows']};baseline=[base[k] for k in SCREEN]
    try:
        for kind in ['layer_control','target']:
            arch=apply(model,parent,patches[kind]);rows=e.coding(model,tok,tasks(SCREEN))
            report['screens'][kind]={'architecture':arch,'rows':rows};save('trial_005.json',report)
        rows=report['screens']['target']['rows']
        if not dominates(flatten(rows),flatten(baseline)):
            report.update(stage='rejected_on_screen',eligible_for_new_validation=False,
                          reason='No monotone execution gain from selective third visit')
        else:
            apply(model,parent);paired=full(model,tok,'parent',5)
            apply(model,parent,patches['target']);candidate=full(model,tok,'target',5)
            history=json.loads((e.HERE/'best_metrics.json').read_text())
            ok,reason=accept_paired(candidate,paired,history)
            report.update(stage='eligible_for_new_validation' if ok else 'rejected_full_gates',
                          eligible_for_new_validation=ok,reason=reason)
    finally:apply(model,parent)
    report['model_process_active']=False;save('trial_005.json',report)
    print('TRIAL_DECISION',5,report['stage'],flush=True)


if __name__=='__main__':main()
