"""Add read-only mHC stream measurements to the frozen hybrid diagnostic."""
from run import *

original_load=e.cr.load
stats={};handles=[]
def measured_load(variant):
    model,meta=original_load(variant)
    if variant=='baseline':
        for i in range(4,28):
            for kind in ['mhc_attn','mhc_ffn']:
                router=getattr(model.model.language_model.layers[i],kind)
                key=f'{i}.{kind}'
                stats[key]={'observations':0,'positions':0,'max_stream_abs_difference':0.,
                    'weight_nonzero':int(router.weight.count_nonzero()),
                    'post_bias_equal':bool(router.bias[2]==router.bias[3])}
                def capture(module,inputs,key=key):
                    x=inputs[0].detach();s=stats[key]
                    s['observations']+=1;s['positions']+=x.numel()//(2*x.shape[-1])
                    s['max_stream_abs_difference']=max(s['max_stream_abs_difference'],float((x[...,0,:]-x[...,1,:]).abs().max()))
                handles.append(router.register_forward_pre_hook(capture))
    return model,meta

e.cr.load=measured_load
try:diagnostic('liquid')
finally:
    for h in handles:h.remove()
    save('router_runtime_audit.json',{'source':'actual unchanged hybrid 512-token greedy diagnostic',
        'intervention':False,'routers':stats,
        'all_streams_equal_in_measured_inputs':bool(stats) and all(s['max_stream_abs_difference']==0 for s in stats.values())})
