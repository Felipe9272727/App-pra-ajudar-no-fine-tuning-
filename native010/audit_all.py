"""Scan every scalar in the real selected model, with bounded-memory reductions."""
import collections
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_flatten

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,torch,e,PARENT_HASH
from native_runtime import SOURCE_LAYERS,IDENTITY_LAYERS
from safetensors import safe_open

CHUNK=1_048_576
BOUNDS=[2.**x for x in [-24,-20,-16,-12,-10,-8,-6,-4,-2,0,2,4,8]]
def save(name,value):e.cr.atomic_json(HERE/name,value)

def donor_name(name):
    m=re.match(r'(model.language_model.layers\.)(\d+)(\..*)',name)
    return m[1]+str(SOURCE_LAYERS[int(m[2])])+m[3] if m else name

@torch.inference_mode()
def inspect_tensor(tensor,reference=None,conv_reference=None):
    t=tensor.detach();was_contiguous=t.is_contiguous()
    if not was_contiguous:t=t.contiguous()
    flat=t.view(-1);n=t.numel();finite=zero=positive=negative=nan=inf=0
    total=total2=0.;minimum=math.inf;maximum=-math.inf;hash_=hashlib.sha256()
    hist=torch.zeros(len(BOUNDS)+1,dtype=torch.int64);bounds=torch.tensor(BOUNDS)
    changed=ref_count=valid_pairs=0;difference2=reference2=0.;maxdifference=0.
    if conv_reference is not None:
        reference=torch.nn.functional.pad(conv_reference,(3,0))
    ref_flat=reference.view(-1) if reference is not None else None
    if ref_flat is not None:assert ref_flat.shape==flat.shape
    for start in range(0,n,CHUNK):
        raw=flat[start:start+CHUNK];hash_.update(raw.contiguous().view(torch.uint8).numpy().tobytes())
        x=raw.float();valid=torch.isfinite(x);xf=x[valid];finite+=int(valid.sum())
        nan+=int(torch.isnan(x).sum());inf+=int(torch.isinf(x).sum())
        zero+=int((xf==0).sum());positive+=int((xf>0).sum());negative+=int((xf<0).sum())
        if len(xf):
            minimum=min(minimum,float(xf.min()));maximum=max(maximum,float(xf.max()))
            xd=xf.double();total+=float(xd.sum());total2+=float(xd.square().sum())
            hist+=torch.bincount(torch.bucketize(xf.abs(),bounds),minlength=len(hist))
        if ref_flat is not None:
            r=ref_flat[start:start+CHUNK];rf=r.float();pair=valid&torch.isfinite(rf)
            changed+=int((raw!=r).sum());ref_count+=len(r)
            valid_pairs+=int(pair.sum());diff=x[pair].double()-rf[pair].double()
            difference2+=float(diff.square().sum());reference2+=float(rf[pair].double().square().sum())
            if len(diff):maxdifference=max(maxdifference,float(diff.abs().max()))
    mean=total/finite if finite else None
    result={'shape':list(t.shape),'dtype':str(t.dtype),'numel':n,'bytes':n*t.element_size(),
        'sha256_values':hash_.hexdigest(),'originally_contiguous':was_contiguous,'finite':finite,'nan':nan,'inf':inf,'zeros':zero,
        'positive':positive,'negative':negative,'min':minimum if finite else None,'max':maximum if finite else None,
        'mean':mean,'std':math.sqrt(max(0,total2/finite-mean*mean)) if finite else None,
        'rms':math.sqrt(total2/finite) if finite else None,'l2':math.sqrt(total2),
        'magnitude_histogram':hist.tolist()}
    assert finite+nan+inf==n and sum(result['magnitude_histogram'])==finite
    if ref_flat is not None:
        result['source_difference']={'compared_values':ref_count,'finite_value_pairs':valid_pairs,'changed_values':changed,
            'l2':math.sqrt(difference2),'relative_l2':math.sqrt(difference2/max(reference2,1e-30)),
            'max_abs':maxdifference,'original_reference_l2':math.sqrt(reference2),
            'alignment':'three zero-padded history taps + original four taps' if conv_reference is not None else 'same shape'}
    return result

@torch.inference_mode()
def matrix_diagnostics(tensor,iterations=6):
    t=tensor.detach();m=t.shape[0];n=t.numel()//m;matrix=t.reshape(m,n)
    block=max(1,CHUNK//n);row2=torch.zeros(m,dtype=torch.float64);col2=torch.zeros(n,dtype=torch.float64)
    for start in range(0,m,block):
        x=matrix[start:start+block].double();row2[start:start+len(x)]=x.square().sum(1);col2+=x.square().sum(0)
    row=row2.sqrt().float();col=col2.sqrt().float();frob2=float(row2.sum())
    spectral=0.;convergence=None
    if frob2>0:
        v=torch.sin(torch.arange(n,dtype=torch.float32)+.37)+torch.cos(torch.arange(n,dtype=torch.float32)*.618+.11)
        v/=v.norm();previous=None
        for _ in range(iterations):
            z=torch.zeros(n);sigma2=0.
            for start in range(0,m,block):
                x=matrix[start:start+block].float();u=x@v;z+=x.T@u;sigma2+=float(u.double().square().sum())
            spectral=math.sqrt(sigma2);convergence=abs(spectral-previous)/max(spectral,1e-30) if previous is not None else None
            previous=spectral
            if float(z.norm())==0:break
            v=z/z.norm()
    return {'row_norms':row,'column_norms':col}, {'flattened_shape':[m,n],
        'zero_rows':int((row==0).sum()),'zero_columns':int((col==0).sum()),
        'min_row_norm':float(row.min()),'max_row_norm':float(row.max()),
        'min_column_norm':float(col.min()),'max_column_norm':float(col.max()),
        'spectral_norm_power_estimate':spectral,'power_iterations':iterations,
        'last_relative_spectral_change':convergence,'stable_rank_upper_estimate':frob2/max(spectral*spectral,1e-30) if spectral else 0.,
        'interpretation':'Full-value row/column norms; approximate spectrum using full matrix products, not exact SVD. Higher-dimensional tensors flattened by first axis.'}

class WeightAccess(TorchDispatchMode):
    def __init__(self,parameters):
        super().__init__();self.names={p.untyped_storage().data_ptr():name for name,p in parameters};self.reads=collections.defaultdict(collections.Counter)
    def __torch_dispatch__(self,func,types,args=(),kwargs=None):
        for value in tree_flatten((args,kwargs or {}))[0]:
            if isinstance(value,torch.Tensor) and value.device.type!='meta':
                name=self.names.get(value.untyped_storage().data_ptr())
                if name:self.reads[name][str(func)]+=1
        return func(*args,**(kwargs or {}))

@torch.inference_mode()
def main():
    assert not (HERE/'audit_complete.json').exists(),'Complete audit already saved; inspect instead of repeating'
    save('status.json',{'status':'auditing_all_weights','model_process_active':True,
        'checkpoint_promoted':False,'parent_sha256':PARENT_HASH,'backward_passes':0})
    model,tok,parent,meta=load();source_path=ROOT/'upstream/model.safetensors-00001-of-00001.safetensors'
    parameters=list(model.named_parameters());all_names=list(model.named_parameters(remove_duplicate=False))
    canonical={id(t):name for name,t in parameters}
    aliases={name:canonical[id(t)] for name,t in all_names if name!=canonical[id(t)]}
    unique_total=sum(p.numel() for _,p in parameters)
    assert unique_total==sum(p.numel() for p in model.parameters())
    groups=collections.defaultdict(lambda:{'tensors':0,'values':0,'zero_values':0,'nonfinite_values':0})
    rows=[];buffers=[];norms={};started=time.monotonic()
    with safe_open(source_path,framework='pt',device='cpu') as source, (HERE/'parameters.jsonl').open('w') as output:
        available=set(source.keys())
        for index,(name,tensor) in enumerate(parameters):
            refname=donor_name(name);reference=None;conv=None
            if refname in available:
                candidate=source.get_tensor(refname)
                if candidate.shape==tensor.shape:reference=candidate
                elif name.endswith('.conv1d.weight') and tensor.shape[-1]==7 and candidate.shape[-1]==4:conv=candidate
            row={'name':name,'original_donor':refname if reference is not None or conv is not None else None,
                **inspect_tensor(tensor,reference,conv)}
            if tensor.ndim>=2 and tensor.numel()>0 and row['nan']+row['inf']==0:
                norms[name],row['matrix_diagnostics']=matrix_diagnostics(tensor)
            row['all_zero']=row['zeros']==row['numel'];row['requires_grad']=tensor.requires_grad
            family='vision' if name.startswith('model.visual.') else ('router' if '.mhc_' in name else ('visit_gain' if name.endswith('native_visit_gain') else 'language'))
            row['family']=family;g=groups[family];g['tensors']+=1;g['values']+=row['numel'];g['zero_values']+=row['zeros'];g['nonfinite_values']+=row['nan']+row['inf']
            output.write(json.dumps(row,allow_nan=False)+'\n');output.flush();rows.append(row)
            if index%25==0:
                save('audit_progress.json',{'tensors_scanned':index+1,'total_tensors':len(parameters),
                    'scalar_values_scanned':sum(r['numel'] for r in rows),'total_scalar_values':unique_total,'last_tensor':name})
                print('FULL_SCAN',index+1,len(parameters),name,flush=True)
            del reference,conv
        for name,tensor in model.named_buffers():buffers.append({'name':name,**inspect_tensor(tensor)})
    byname={r['name']:r for r in rows};neutral=[];layer_summary=[]
    for i,layer in enumerate(model.model.language_model.layers):
        prefix=f'model.language_model.layers.{i}.';members=[r for r in rows if r['name'].startswith(prefix)]
        attn='linear_attn.out_proj.weight' if hasattr(layer,'linear_attn') else 'self_attn.o_proj.weight'
        dead=byname[prefix+'mlp.down_proj.weight']['all_zero'] and byname[prefix+attn]['all_zero']
        if dead:neutral.append(i)
        layer_summary.append({'physical_layer':i,'original_donor':SOURCE_LAYERS[i],'parameters':sum(r['numel'] for r in members),
            'both_branch_outputs_zero':dead,'visit_gains':layer.native_visit_gain.tolist() if hasattr(layer,'native_visit_gain') else [1.],
            'window':getattr(layer,'_native_window',None),'changed_from_donor_values':sum(r.get('source_difference',{}).get('changed_values',0) for r in members)})
    routers=[r for r in rows if '.mhc_' in r['name'] and r['name'].endswith('.weight')]
    probe='Descreva o objetivo de verificar uma hipótese com evidências.'
    access=WeightAccess(parameters)
    ids=e.cr.prompt(tok,probe)
    nonfinite=sum(r['nan']+r['inf'] for r in rows)
    if not nonfinite:
        with access:
            pre=model(input_ids=ids,use_cache=True,logits_to_keep=1)
            own=pre.logits[:,-1].argmax(-1,keepdim=True)
            model(input_ids=own,past_key_values=pre.past_key_values,use_cache=True,logits_to_keep=1)
    save('weight_access.json',{'probe':probe,'generated_tokens_used':1,'correct_answer_supplied':False,
        'method':'TorchDispatch parameter-storage reads during text prefill and one own next-token step',
        'observed_parameters':{name:dict(counts) for name,counts in access.reads.items()},
        'not_observed':[name for name,_ in parameters if name not in access.reads],
        'limitation':'Observed reads do not prove contribution to output; vision non-use is expected in a text-only probe.'})
    temporal=[]
    for i,layer in enumerate(model.model.language_model.layers):
        if not hasattr(layer,'linear_attn') or nonfinite:continue
        block=layer.linear_attn;w=block.conv1d.weight.detach().float()[:,0,:]
        temporal.append({'physical_layer':i,'kernel':w.shape[-1],
            'history_nonzero':int(w[:,:3].count_nonzero()),'history_relative_norm':float(w[:,:3].norm()/w.norm().clamp_min(1e-20)),
            'kernel_l1_min':float(w.abs().sum(1).min()),'kernel_l1_max':float(w.abs().sum(1).max()),
            'dc_gain_min':float(w.sum(1).min()),'dc_gain_max':float(w.sum(1).max()),
            'A_log_min':float(block.A_log.min()),'A_log_max':float(block.A_log.max()),
            'dt_bias_min':float(block.dt_bias.min()),'dt_bias_max':float(block.dt_bias.max())})
    try:architecture=e.cr.check_architecture(model,parent['passes'])
    except AssertionError as error:architecture={'check_failed':True,'detail':str(error)}
    result={'status':'complete' if not nonfinite else 'complete_with_nonfinite_values','selected_checkpoint':'rsi100/checkpoints/best.pt','parent_sha256':PARENT_HASH,
        'unique_parameter_tensors':len(parameters),'unique_parameter_values':unique_total,'parameter_names_with_aliases':len(all_names),
        'previously_recorded_parameter_values':1020252592,'matches_prior_parameter_count':unique_total==1020252592,
        'aliases':aliases,'buffer_tensors':len(buffers),'buffer_values':sum(r['numel'] for r in buffers),
        'every_parameter_scalar_scanned':sum(r['numel'] for r in rows)==unique_total,
        'nonfinite_parameter_values':sum(r['nan']+r['inf'] for r in rows),'all_zero_parameter_tensors':[r['name'] for r in rows if r['all_zero']],
        'groups':dict(groups),'magnitude_histogram_upper_bounds':BOUNDS,'layers':layer_summary,
        'neutral_physical_layers':neutral,'parameters_in_neutral_layers':sum(x['parameters'] for x in layer_summary if x['both_branch_outputs_zero']),
        'router_input_weight_tensors':len(routers),'router_input_nonzero_weights':sum(r['numel']-r['zeros'] for r in routers),
        'text_probe_observed_parameters':len(access.reads),'temporal_layers':temporal,
        'reference_compared_values':sum(r.get('source_difference',{}).get('compared_values',0) for r in rows),
        'reference_changed_values':sum(r.get('source_difference',{}).get('changed_values',0) for r in rows),
        'architecture':architecture,'elapsed_seconds':time.monotonic()-started,
        'interpretation':'Complete scalar audit, not unique causal error attribution or intelligence measurement'}
    assert result['every_parameter_scalar_scanned']
    e.tensor_checkpoint(norms,HERE/'row_column_norms.pt')
    save('buffers.json',buffers);save('audit_complete.json',result)
    save('status.json',{'status':'audit_complete_native_design_pending','model_process_active':False,
        'checkpoint_promoted':False,'parent_sha256':PARENT_HASH,'backward_passes':0})
    print('ALL_WEIGHTS_AUDITED',len(parameters),unique_total,neutral,flush=True)

if __name__=='__main__':main()
