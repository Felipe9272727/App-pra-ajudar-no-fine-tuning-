"""Finite native architecture ablation: source-only activations, no solutions."""
import argparse,json,sys,time,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import e,torch,load,tensor_checkpoint,PARENT_HASH,tasks
from native010.native_runtime import SOURCE_LAYERS,depth_warmstart,build,architecture,modified_parameters,tensor_hash,verify_bundle
from policy import flatten,dominates
import torch.nn.functional as F

def save(name,obj):e.cr.atomic_json(HERE/name,obj)
def state(status,active=False):save('status.json',{'status':status,'model_process_active':active,'checkpoint_promoted':False,'parent_sha256':PARENT_HASH,'backward_passes':0})
def verify():
    frozen=json.loads((HERE/'native_frozen.json').read_text())
    for p,h in frozen['files'].items():assert e.cr.file_hash(ROOT/p)==h,p

def episodes():return json.loads((ROOT/'reasoning/multi008/inputs.json').read_text())['episodes']
def ids(tok,ep):return e.cr.prompt(tok,ep['input']) if ep['kind']=='coding_prompt' else tok(ep['input'],return_tensors='pt',add_special_tokens=False)['input_ids']
def positions(n):return torch.linspace(0,n-1,min(12,n)).round().long().unique()
def freeze():
    assert not (HERE/'native_frozen.json').exists()
    paths=['native010/NATIVE_PROTOCOL.md','native010/native_runtime.py','native010/study.py','reasoning/multi008/inputs.json','reasoning/runtime_helpers.py','v2_adaptation/native_runtime.py','modeling_sensenova_loop.py','code_rsi/runtime.py','rsi100/engine.py','rsi100/data.json','local_cpu/sandbox.py','rsi100/checkpoints/best.pt']
    save('native_frozen.json',{'files':{p:e.cr.file_hash(ROOT/p) for p in paths},'quality_outputs_observed':False,'variants':['depth','liquid','routed']})

@torch.inference_mode()
def teacher():
    verify();assert not (HERE/'teacher_targets.pt').exists();state('collect_teacher_convolution',True)
    model,meta=e.cr.load('original');tok=e.cr.tokenizer();targets={};current={};handles=[]
    for i,l in enumerate(model.model.language_model.layers):
        if not hasattr(l,'linear_attn'):continue
        def hook(module,inputs,output,i=i,l=l):
            x=output.detach().float().transpose(1,2);w=l.linear_attn.conv1d.weight.float()
            y=F.conv1d(x,w,padding=w.shape[-1]-1,groups=w.shape[0])[...,:x.shape[-1]]
            current[i]=y[0,:,positions(x.shape[-1])].T.contiguous().to(torch.bfloat16)
        handles.append(l.linear_attn.in_proj_qkv.register_forward_hook(hook))
    for ep in episodes():
        current.clear();x=ids(tok,ep);model(input_ids=x,use_cache=False,logits_to_keep=1)
        targets[ep['id']]={i:v.clone() for i,v in current.items()};print('TEACHER',ep['id'],x.shape[-1],flush=True)
    for h in handles:h.remove()
    tensor_checkpoint(targets,HERE/'teacher_targets.pt')
    save('teacher_targets.json',{'status':'complete','input_count':len(targets),'sha256':e.cr.file_hash(HERE/'teacher_targets.pt'),'reference_solution_generated':False,'internal_numeric_targets_only':True})
    state('teacher_complete')

@torch.inference_mode()
def liquid():
    verify();assert not (HERE/'checkpoints/liquid.pt').exists();state('fit_liquid',True)
    model,tok,parent,meta=load();depth_warmstart(model)
    targets=torch.load(HERE/'teacher_targets.pt',weights_only=True);stats={};current=None;handles=[]
    for i,l in enumerate(model.model.language_model.layers):
        if not hasattr(l,'linear_attn'):continue
        c=l.linear_attn.conv1d.weight.shape[0]
        stats[i]={'G':torch.zeros(c,7,7),'b':torch.zeros(c,7),'n':0.}
        def hook(module,inputs,output,i=i):
            x=output.detach().float().transpose(1,2)
            lag=F.pad(x,(6,0)).unfold(-1,7,1)[0,:,positions(x.shape[-1]),:]
            y=targets[current][SOURCE_LAYERS[i]].float().T
            weight=.5 if 4<=i<28 else 1.
            stats[i]['G'].add_(torch.einsum('csk,csl->ckl',lag,lag),alpha=weight)
            stats[i]['b'].add_(torch.einsum('csk,cs->ck',lag,y),alpha=weight)
            stats[i]['n']+=lag.shape[1]*weight
        handles.append(l.linear_attn.in_proj_qkv.register_forward_hook(hook))
    for ep in episodes():
        current=ep['id'];model(input_ids=ids(tok,ep),use_cache=False,logits_to_keep=1);print('LIQUID_STATS',current,flush=True)
    for h in handles:h.remove()
    patch={};report={}
    for i,s in stats.items():
        w=model.model.language_model.layers[i].linear_attn.conv1d.weight
        prior=w[:,0,:].float();G=s['G']/s['n'];b=s['b']/s['n'];lam=.1*G.diagonal(dim1=-2,dim2=-1).mean(-1)+1e-6
        fit=torch.linalg.solve(G+lam[:,None,None]*torch.eye(7),b+lam[:,None]*prior)
        delta=fit-prior;relative=delta.norm(dim=-1)/prior.norm(dim=-1).clamp_min(1e-12)
        delta*=torch.minimum(torch.ones_like(relative),.05/relative.clamp_min(1e-12))[:,None]
        delta[relative<.001]=0
        written=(prior+delta).to(w.dtype).unsqueeze(1);assert torch.isfinite(written).all()
        key=f'model.language_model.layers.{i}.linear_attn.conv1d.weight';patch[key]=written
        actual=(written[:,0,:].float()-prior).norm(dim=-1)/prior.norm(dim=-1).clamp_min(1e-12)
        report[str(i)]={'changed_values':int((written!=w).sum()),'max_relative_channel_change_after_quantization':float(actual.max()),'mean_relative_channel_change':float(actual.mean()),'positions':s['n']}
    tensor_checkpoint(patch,HERE/'checkpoints/liquid.pt');tensor_checkpoint(stats,HERE/'liquid_statistics.pt')
    save('liquid_fit.json',{'status':'complete','per_layer':report,'sha256':e.cr.file_hash(HERE/'checkpoints/liquid.pt'),'solver':'closed-form per-channel ridge','no_gradient':True})
    state('liquid_complete')

@torch.inference_mode()
def routed():
    verify();assert not (HERE/'checkpoints/routers.pt').exists();state('fit_routing',True)
    model,tok,parent,meta=load();build(model,'liquid',HERE);states={};handles=[]
    for i,l in enumerate(model.model.language_model.layers[4:28],4):
        for kind in ['mhc_attn','mhc_ffn']:
            key=f'model.language_model.layers.{i}.{kind}'
            states[key]={0:[],1:[]}
            def hook(module,inputs,key=key,l=l):
                x=inputs[0][0,-1].detach().float().flatten();x=x*torch.rsqrt(x.square().mean()+1e-6)
                states[key][int(l._last_native_visit)].append(x)
            handles.append(getattr(l,kind).register_forward_pre_hook(hook))
    for ep in episodes():
        model(input_ids=ids(tok,ep),use_cache=False,logits_to_keep=1);print('ROUTE_STATS',ep['id'],flush=True)
    for h in handles:h.remove()
    params=dict(model.named_parameters());patch={};report={}
    for key,s in states.items():
        first=torch.stack(s[0]);second=torch.stack(s[1]);X=torch.cat([first,second]);v=(second-first).mean(0)
        p=X@v;center=p.mean();bound=(p-center).abs().max()
        if float(bound)<1e-12:continue
        v=v*(.125/bound);b=-center*(.125/bound)
        coeff=torch.tensor([-.5,.5,-1.,1.,.25,-.25,-.25,.25])
        W=coeff[:,None]*v[None,:];bias=params[key+'.bias'].clone()+coeff*b
        patch[key+'.weight']=W;patch[key+'.bias']=bias
        q=X@v+b
        report[key]={'calibration_abs_q_max':float(q.abs().max()),'first_mean_q':float(q[:len(first)].mean()),'second_mean_q':float(q[len(first):].mean()),'direction_norm':float(v.norm())}
    tensor_checkpoint(patch,HERE/'checkpoints/routers.pt');tensor_checkpoint(states,HERE/'router_states.pt')
    save('router_fit.json',{'status':'complete','routers':report,'sha256':e.cr.file_hash(HERE/'checkpoints/routers.pt'),'unlabelled_inputs':19})
    state('routing_complete')

@torch.inference_mode()
def checkpoint(variant):
    verify();model,tok,parent,meta=load()
    original={n:tensor_hash(p) for n,p in modified_parameters(model,variant).items()}
    old={n:p.detach().clone() for n,p in modified_parameters(model,variant).items()}
    arch=build(model,variant,HERE);modified=modified_parameters(model,variant)
    report={'variant':variant,'parent_sha256':PARENT_HASH,'format':'complete deterministic incremental reconstruction; not monolithic safetensors',
        'recipe':'native010.native_runtime.build after immutable parent load','architecture':arch,
        'parent_tensor_hashes':original,'modified_tensor_hashes':{n:tensor_hash(p) for n,p in modified.items()},
        'actual_changed_values':sum(int((p!=old[n]).sum()) for n,p in modified.items()),
        'actual_changed_tensors':sum(not torch.equal(p,old[n]) for n,p in modified.items()),
        'source_manifest_sha256':e.cr.file_hash(HERE/'native_frozen.json'),
        'overlay_sha256':{p.name:e.cr.file_hash(p) for p in [HERE/'checkpoints/liquid.pt',HERE/'checkpoints/routers.pt'] if p.exists() and (p.name=='liquid.pt' and variant in ['liquid','routed'] or p.name=='routers.pt' and variant=='routed')}}
    save(f'checkpoint_{variant}.json',report);print('CHECKPOINT',variant,report['actual_changed_values'],flush=True)
    state('checkpoint_'+variant+'_saved')

@torch.inference_mode()
def technical(variant):
    verify();state('technical_'+variant,True);model,tok,parent,meta=load();arch=build(model,variant,HERE)
    verify_bundle(model,variant,HERE);probes=[]
    text='A careful reader checks assumptions and records the sequence of observations. '
    raw=tok(text*120,return_tensors='pt',add_special_tokens=False)['input_ids']
    for n in [17,257,513]:
        x=raw[:,:n]
        a=model(input_ids=x,use_cache=False,logits_to_keep=1).logits[:,-1].float()
        pre=model(input_ids=x[:,:-1],use_cache=True,logits_to_keep=1)
        step=model(input_ids=x[:,-1:],past_key_values=pre.past_key_values,use_cache=True,logits_to_keep=1).logits[:,-1].float()
        d={'length':n,'max_logit_difference':float((a-step).abs().max()),'same_top_token':bool(a.argmax()==step.argmax()),'finite':bool(torch.isfinite(a).all() and torch.isfinite(step).all())}
        d['passed']=d['finite'] and d['same_top_token'] and d['max_logit_difference']<=.5
        probes.append(d);print('CACHE',variant,d,flush=True)
    save(f'technical_{variant}.json',{'status':'complete','cold_reconstruction_bitwise_verified':True,'architecture':arch,'probes':probes,'passed':all(p['passed'] for p in probes)})
    state('technical_'+variant+'_complete')

SCREEN=['prefix_sums','rotate_right','longest_run','overlap_count','sum_abs','palindrome','binary_search']
@torch.inference_mode()
def evaluate(variant,full=False):
    verify();state(('full_' if full else 'screen_')+variant,True)
    if variant in ['original','parent']:
        model,meta=e.cr.load('original' if variant=='original' else 'baseline');tok=e.cr.tokenizer()
        if variant=='parent':e.apply(model,e.read_checkpoint('best.pt'))
    else:
        technical=json.loads((HERE/f'technical_{variant}.json').read_text());assert technical['passed']
        model,tok,parent,meta=load();meta['architecture']=build(model,variant,HERE);verify_bundle(model,variant,HERE)
    name=f'{"full" if full else "screen"}_{variant}.json';path=HERE/name
    r=json.loads(path.read_text()) if path.exists() else {'status':'running','variant':variant,'model':meta,'rows':[],
        'protocol':{'max_new_tokens':160,'greedy':True,'thinking':False,'cpu_threads':4,'no_answers_in_input':True,'data_sha256':e.DATA_HASH},'controls':[]}
    rows=e.DATA['search']+e.DATA['guard'] if full else tasks(SCREEN)
    for row in rows:
        if row['id'] not in {x['id'] for x in r['rows']}:
            r['rows']+=e.coding(model,tok,[row]);save(name,r)
    if full:
        for row in e.DATA['search_controls']:
            if row['id'] not in {x['id'] for x in r['controls']}:r['controls']+=e.quality(model,tok,[row]);save(name,r)
        r['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
    r['tasks_passed']=sum(x['all_passed'] for x in r['rows']);r['cases_passed']=sum(x['passed'] for x in r['rows']);r['total_cases']=sum(x['total'] for x in r['rows']);r['status']='complete';save(name,r)
    state(name+'_complete')

def decide():
    results={}
    parent=json.loads((HERE/'screen_parent.json').read_text());original=json.loads((HERE/'screen_original.json').read_text())
    for variant in ['depth','liquid','routed']:
        p=HERE/f'screen_{variant}.json'
        if not p.exists():continue
        r=json.loads(p.read_text());assert r['status']=='complete'
        b=flatten(parent['rows']);a=flatten(r['rows']);assert set(a)==set(b);wins=sum(a[k] and not b[k] for k in b);losses=sum(b[k] and not a[k] for k in b)
        results[variant]={'tasks':r['tasks_passed'],'cases':r['cases_passed'],'wins':wins,'losses':losses,'full_development_eligible':wins>0 and losses==0 and r['tasks_passed']>=parent['tasks_passed']}
    save('screen_comparison.json',{'parent':{'tasks':parent['tasks_passed'],'cases':parent['cases_passed']},'original':{'tasks':original['tasks_passed'],'cases':original['cases_passed']},'candidates':results,'independent_validation_opened':False,'checkpoint_promoted':False})
    print(json.dumps(results,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','teacher','liquid','routed','checkpoint','technical','screen','full','decide']);p.add_argument('variant',nargs='?');a=p.parse_args()
    if a.phase in ['freeze','teacher','liquid','routed','decide']:globals()[a.phase]()
    elif a.phase=='checkpoint':checkpoint(a.variant)
    elif a.phase=='technical':technical(a.variant)
    else:evaluate(a.variant,a.phase=='full')
