"""Post-hoc parameter geometry only: does not generate, train or select."""
from core import *


def category(name):
    if '.mhc_' in name:return 'mHC'
    if 'native_visit_gain' in name:return 'visit_gains'
    if '.conv1d.' in name:return 'temporal_convolution'
    if '.in_proj_a.' in name or '.in_proj_b.' in name:return 'temporal_input_gates'
    if name.endswith(('.A_log','.dt_bias')):return 'temporal_decay'
    return 'normalization'


def main():
    assert read('status.json')['status']=='complete' and not read('runtime.json')['model_process_active']
    verify_frozen();torch.set_num_threads(4)
    initial,_=load_parts(H/'checkpoints/initial_factors');base=initial['native'];del initial
    result={'scope':'post-hoc parameter changes; not isolated thinking weights or proof of useful routing','stages':{}}
    for stage in ['sft_epoch1','sft_final','policy_final']:
        state,manifest=load_parts(H/'checkpoints'/stage);audit=read('reports/'+stage+'.json');groups={};gains={};routers=[]
        for name,value in state['native'].items():
            old=base[name];delta=value.float()-old.float();den=max(float(old.double().norm()),math.sqrt(old.numel())*.01)
            relative=float(delta.double().norm())/den;assert relative<=.005+1e-7/den
            kind=category(name);g=groups.setdefault(kind,{'tensors':0,'values':0,'changed_tensors':0,'changed_values':0,'max_relative_L2_with_floor':0.})
            changed=int((value!=old).count_nonzero());g['tensors']+=1;g['values']+=value.numel();g['changed_tensors']+=changed>0;g['changed_values']+=changed;g['max_relative_L2_with_floor']=max(g['max_relative_L2_with_floor'],relative)
            if 'native_visit_gain' in name:
                assert bool((value>0).all()) and abs(float(value.sum())-1)<1e-6
                gains[name]={'parent':old.tolist(),'candidate':value.tolist()}
            if name.endswith(('.mhc_attn.weight','.mhc_ffn.weight')):routers.append({'name':name,'parent_norm':float(old.norm()),'candidate_norm':float(value.norm())})
        formerly_neutral=[]
        for name,v in audit['projection_changes'].items():
            physical=int(name.split('.')[3])
            if physical in list(range(8,12))+list(range(20,24)) and name.endswith(('.mlp.down_proj.weight','.linear_attn.out_proj.weight','.self_attn.o_proj.weight')):
                formerly_neutral.append({'name':name,**v})
        result['stages'][stage]={'native_groups':groups,'visit_gain_values':gains,'mHC_input_matrices':routers,
            'formerly_neutral_exit_matrices':formerly_neutral,'formerly_neutral_exits_changed':sum(v['changed_values']>0 for v in formerly_neutral),
            'folded_projection_values_changed':sum(v['changed_values'] for v in audit['projection_changes'].values()),
            'extra_deployed_factor_parameters':0,'native_loaded_parameters':audit['effective_native_parameter_count'],
            'checkpoint_sha256':manifest['compressed_sha256']}
        del state;gc.collect()
    save('reports/parameter_geometry.json',result);print('ARCHIVE028_GEOMETRY_COMPLETE_NO_MODEL_GENERATION')
if __name__=='__main__':main()
