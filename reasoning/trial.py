"""Two authored hypotheses, actual parameter overwrites and strict rollback."""
import argparse
import json
from runtime_helpers import *
from policy import dominates, flatten, accept_paired

SCREEN = ['prefix_sums','rotate_right','longest_run','sum_abs','palindrome','binary_search']


@torch.inference_mode()
def full(model,tok,variant,number):
    path=HERE/f'trial_{number:03d}_{variant}_full.json'
    report=json.loads(path.read_text()) if path.exists() else {'rows':[],'controls':[],'status':'running'}
    seen={r['id'] for r in report['rows']}
    for task in e.DATA['search']+e.DATA['guard']:
        if task['id'] not in seen:
            report['rows']+=e.coding(model,tok,[task]);save(path.name,report)
    seen={r['id'] for r in report['controls']}
    for row in e.DATA['search_controls']:
        if row['id'] not in seen:
            report['controls']+=e.quality(model,tok,[row]);save(path.name,report)
    report['control_bits']=[x['correct'] for x in report['controls']]
    if 'anchor_nll' not in report:
        report['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
    report['status']='complete';save(path.name,report)
    return report


@torch.inference_mode()
def make_loop(number,diag):
    assert number==3
    patches={}
    for kind,key in [('target','target_layers'),('layer_control','control_layers')]:
        patch={'parent_sha256':PARENT_HASH,'hypothesis':3,'kind':kind,
               'layer_visit_gains':{str(i):torch.tensor([.925,.075],dtype=torch.float32) for i in diag[key]}}
        path=HERE/f'checkpoints/trial_003_{kind}.pt';tensor_checkpoint(patch,path)
        patches[kind]=patch
    return patches,{'target_layers':diag['target_layers'],'control_layers':diag['control_layers'],
                    'dose':[.925,.075],'architecture_passes':2,'edited_parameter_family':'native_visit_gain'}


@torch.inference_mode()
def make_dense(model,tok,parent):
    traces=torch.load(HERE/'traces.pt',weights_only=True)
    own=traces['rotate_right'];text=own['output'];ids=own['token_ids'].tolist()
    marker='return xs[k:]';assert marker in text,'Inspect actual erroneous program before choosing a new target'
    char=text.index('k',text.index(marker))
    boundaries=[len(tok.decode(ids[:i],skip_special_tokens=True)) for i in range(len(ids)+1)]
    index=next(i for i in range(len(ids)) if boundaries[i]<=char<boundaries[i+1])
    bad=ids[index];assert 'k' in tok.decode([bad])
    h=own['states'][index]
    p=torch.cat([own['states'][:index]]+[traces[k]['states'] for k in ['sum_abs','palindrome','binary_search']])
    ridge=1e-5*float(p.square().sum(1).mean())
    v=h-p.T@torch.linalg.solve(p@p.T+ridge*torch.eye(len(p)),p@h)
    residual_ratio=float(v.norm()/h.norm())
    info={'target_task':'rotate_right','bad_token':bad,'bad_piece':tok.decode([bad]),'target_index':index,
          'preserved_activation_count':len(p),'residual_ratio':residual_ratio,'chosen_fraction':.006,
          'edited_tensor':'model.language_model.layers.31.mlp.down_proj.weight',
          'correct_replacement_or_solution_supplied':False}
    if residual_ratio<.05:
        info['abort_reason']='Residual direction below predeclared stability threshold'
        return {},info
    v/=v.norm();u=model.get_output_embeddings().weight[bad].detach().float().clone();u/=u.norm()
    written=(parent['dense_weight'].float()-.006*parent['dense_weight'].float().norm()*torch.outer(u,v)).to(parent['dense_weight'].dtype)
    patch={'parent_sha256':PARENT_HASH,'hypothesis':4,'dense_weight':written}
    info.update(actual_relative_norm=float((written.float()-parent['dense_weight'].float()).norm()/parent['dense_weight'].float().norm()),
        changed_values=int((written!=parent['dense_weight']).sum()),
        max_normalized_preservation_projection=float((p@v/p.norm(dim=1)).abs().max()))
    tensor_checkpoint({'input_direction':v,'negative_output_direction':u,'preservation_states':p,'target_state':h},HERE/'directions_004.pt')
    tensor_checkpoint(patch,HERE/'checkpoints/trial_004_target.pt')
    return {'target':patch},info


@torch.inference_mode()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('number',type=int,choices=[3,4]);a=parser.parse_args()
    report_path=HERE/f'trial_{a.number:03d}.json'
    assert not report_path.exists(),'Trial already has a durable/local result; inspect instead of duplicating'
    diag=json.loads((HERE/'diagnostic.json').read_text());assert diag['status']=='complete'
    model,tok,parent,meta=load()
    patches,info=make_loop(a.number,diag) if a.number==3 else make_dense(model,tok,parent)
    previous={r['id']:r for r in diag['rows']};baseline=[previous[k] for k in SCREEN]
    report={'trial':a.number,'stage':'constructed','parent_sha256':PARENT_HASH,'metadata':info,
            'screens':{},'backward_passes':0,'fresh_benchmark_used':False,'checkpoint_promoted':False}
    save(report_path.name,report)
    if not patches:
        report.update(stage='aborted_unstable_direction',eligible_for_new_validation=False)
        save(report_path.name,report);return
    order=['layer_control','target'] if a.number==3 else ['target']
    try:
        for kind in order:
            architecture=apply(model,parent,patches[kind]);measured=e.coding(model,tok,tasks(SCREEN))
            report['screens'][kind]={'rows':measured,'architecture':architecture}
            save(report_path.name,report)
        measured=report['screens']['target']['rows']
        if not dominates(flatten(measured),flatten(baseline)):
            report.update(stage='rejected_on_screen',eligible_for_new_validation=False,
                          reason='No strict case gain with full retention of six-task screen')
        else:
            apply(model,parent);paired=full(model,tok,'parent',a.number)
            apply(model,parent,patches['target']);candidate=full(model,tok,'target',a.number)
            history=json.loads((e.HERE/'best_metrics.json').read_text())
            accepted,reason=accept_paired(candidate,paired,history)
            report.update(stage='eligible_for_new_validation' if accepted else 'rejected_full_gates',
                          eligible_for_new_validation=accepted,reason=reason)
    finally:
        apply(model,parent)
    report['model_process_active']=False
    save(report_path.name,report)
    print('TRIAL_DECISION',a.number,report['stage'],flush=True)


if __name__=='__main__':main()
