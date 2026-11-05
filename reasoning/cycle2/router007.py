"""Mean-preserving stream differentiation with an inverse-sign control."""
from run import *

def apply_patch(model,parent,patch=None):
    arch=apply(model,parent)
    if patch:
        assert patch['parent_sha256']==PARENT_HASH
        bias=model.model.language_model.layers[25].mhc_ffn.bias
        assert bias.dtype==torch.float32
        bias.copy_(patch['router_bias']['25.mhc_ffn'])
    arch['layer25_ffn_post_logits']=model.model.language_model.layers[25].mhc_ffn.bias[2:4].tolist()
    return arch

def full(model,tok,name):
    path=HERE/f'trial_007_{name}_full.json'
    r={'rows':[],'controls':[],'status':'running'}
    for task in e.DATA['search']+e.DATA['guard']:
        r['rows']+=e.coding(model,tok,[task]);save(path.name,r)
    for row in e.DATA['search_controls']:
        r['controls']+=e.quality(model,tok,[row]);save(path.name,r)
    r['control_bits']=[x['correct'] for x in r['controls']]
    r['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
    r['status']='complete';save(path.name,r);return r

@torch.inference_mode()
def main():
    verify();assert not (HERE/'trial_007.json').exists(),'Inspect saved outcome instead of repeating'
    assert json.loads((HERE/'trial_006.json').read_text())['stage']=='rejected_full_gates'
    assert json.loads((HERE/'validation_frozen.json').read_text())['candidate_trials']==[]
    audit=json.loads((HERE/'router_static_audit.json').read_text())
    assert all(x['nonzero']==0 for x in audit['tensors']) and audit['parent_post_bias_nonzero']==0
    status(status='router007',model_process_active=True)
    model,tok,parent,_=load();patches={}
    for name,values in [('inverse_control',[.2,-.2]),('target',[-.2,.2])]:
        bias=parent['router_bias']['25.mhc_ffn'].clone();assert not bool(bias[2:4].any())
        before=bias.clone();bias[2:4]=torch.tensor(values,dtype=torch.float32)
        assert int((bias!=before).sum())==2
        patch={'parent_sha256':PARENT_HASH,'hypothesis':7,'kind':name,'router_bias':{'25.mhc_ffn':bias}}
        tensor_checkpoint(patch,HERE/f'checkpoints/trial_007_{name}.pt');patches[name]=patch
    report={'trial':7,'stage':'constructed','backward_passes':0,'screens':{},
        'parent_sha256':PARENT_HASH,'checkpoint_promoted':False,
        'metadata':{'edited_tensor':'model.language_model.layers.25.mhc_ffn.bias',
            'changed_parameter_indices':[2,3],'target_values':[-.2,.2],
            'inverse_control_values':[.2,-.2],'changed_parameter_count':2,
            'precision':'FP32','output_gains':(2*torch.sigmoid(torch.tensor([-.2,.2]))).tolist(),
            'correct_targets_or_solutions_supplied':False,
            'hypothesis':'break identical-stream symmetry before later layers; not trained thinking'}}
    save('trial_007.json',report)
    baseline_bank={r['id']:r for r in json.loads((HERE/'trial_006_parent_full.json').read_text())['rows']}
    baseline=[baseline_bank[x] for x in SCREEN]
    try:
        for name in ['inverse_control','target']:
            arch=apply_patch(model,parent,patches[name]);stream={'observations':0,'max_abs_difference':0.}
            def capture(module,inputs):
                x=inputs[0];stream['observations']+=1
                stream['max_abs_difference']=max(stream['max_abs_difference'],float((x[...,0,:]-x[...,1,:]).abs().max()))
            handle=model.model.language_model.layers[26].mhc_attn.register_forward_pre_hook(capture)
            try:rows=e.coding(model,tok,tasks(SCREEN))
            finally:handle.remove()
            bits=flatten(rows);oldbits=flatten(baseline)
            report['screens'][name]={'rows':rows,'architecture':arch,'layer26_stream_input_difference':stream,
                'case_wins':sum(v and not oldbits[k] for k,v in bits.items()),
                'case_losses':sum(not v and oldbits[k] for k,v in bits.items())}
            save('trial_007.json',report)
        measured=report['screens']['target']['rows']
        if not dominates(flatten(measured),flatten(baseline)):
            report.update(stage='rejected_on_screen',eligible_for_new_validation=False,
                reason='No strict screen gain with complete case retention')
        else:
            apply_patch(model,parent);paired=full(model,tok,'parent')
            apply_patch(model,parent,patches['target']);candidate=full(model,tok,'target')
            accepted,reason=accept_paired(candidate,paired,json.loads((ROOT/'rsi100/best_metrics.json').read_text()))
            report.update(stage='eligible_for_new_validation' if accepted else 'rejected_full_gates',
                eligible_for_new_validation=accepted,reason=reason)
    finally:apply_patch(model,parent)
    report['model_process_active']=False;save('trial_007.json',report)
    status(status='router007_'+report['stage'],model_process_active=False)
    print('TRIAL007',report['stage'],report['reason'],flush=True)

if __name__=='__main__':main()
