"""Protected multi-layer vector transport from unlabelled prompt activations."""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import e,torch,load,apply as apply_parent,tasks,PARENT_HASH,tensor_checkpoint
from policy import flatten,dominates,accept_paired
from native_runtime import SOURCE_LAYERS

LAYERS=[5,13,25,31]
SCREEN=['prefix_sums','rotate_right','longest_run','overlap_count','sum_abs','palindrome','binary_search']
INPUTS=ROOT/'reasoning/multi008/inputs.json'
def save(name,value):e.cr.atomic_json(HERE/name,value)
def state(**kw):
    d=json.loads((HERE/'status.json').read_text());d.update(kw,updated_unix=time.time());save('status.json',d)
def weight(model,i):return model.model.language_model.layers[i].mlp.down_proj.weight
def tensor_hash(w):return hashlib.sha256(w.detach().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
def snapshot(model):return {str(i):weight(model,i).detach().clone() for i in LAYERS}
def ids(tok,ep):
    return e.cr.prompt(tok,ep['input']) if ep['kind']=='coding_prompt' else tok(ep['input'],return_tensors='pt',add_special_tokens=False)['input_ids']
def verify():
    for p,h in json.loads((HERE/'frozen.json').read_text())['files'].items():assert e.cr.file_hash(ROOT/p)==h,p
def initialize():
    names=['reasoning/multi009/PROTOCOL.md','reasoning/multi009/study009.py','reasoning/multi009/validate009.py',
        'reasoning/multi008/inputs.json','reasoning/multi008/trial_008.json','reasoning/runtime_helpers.py',
        'rsi100/data.json','rsi100/engine.py','rsi100/policy.py','code_rsi/runtime.py',
        'v2_adaptation/native_runtime.py','local_cpu/sandbox.py','rsi100/checkpoints/best.pt']
    save('frozen.json',{'files':{p:e.cr.file_hash(ROOT/p) for p in names},'layers':LAYERS,
        'damping':.25,'ridge_fraction':.01,'relative_norm_cap':.002,'quantized_norm_abort':.003,
        'quality_outputs_observed':False,'validation_observed':False})

class Capture:
    def __init__(self,model,original=False):
        self.model=model;self.original=original;self.values={};self.handles=[]
        for i in LAYERS:
            module=model.model.language_model.layers[SOURCE_LAYERS[i] if original else i].mlp.down_proj
            def hook(module,inputs,output,i=i):
                layer=self.model.model.language_model.layers[i] if not self.original else None
                visit=int(layer._last_native_visit) if layer is not None and 4<=i<28 else 0
                g=float(layer.native_visit_gain[visit]) if layer is not None and 4<=i<28 else 1.
                n=output.shape[1];pos=torch.linspace(0,n-1,steps=min(12,n)).round().long().unique()
                x=inputs[0][0,pos].detach().float().clone();y=output[0,pos].detach().float().clone()
                assert torch.isfinite(x).all() and torch.isfinite(y).all()
                key=str(i)
                if key not in self.values:self.values[key]={'positions':pos,'x':x*g,'y':y*g}
                else:
                    self.values[key]['x']+=x*g;self.values[key]['y']+=y*g
            self.handles.append(module.register_forward_hook(hook))
    def reset(self):self.values={}
    def close(self):
        for h in self.handles:h.remove()

@torch.inference_mode()
def collect(variant):
    verify();name=f'collect_{variant}.json';rp=HERE/name
    report=json.loads(rp.read_text()) if rp.exists() else {'variant':variant,'status':'running','input_ids':[],
        'correct_or_generated_solutions_in_context':False}
    if report['status']=='complete':return
    state(status='collect_'+variant,model_process_active=True)
    payloads={str(i):torch.load(HERE/f'collect_{variant}_layer_{i:02d}.pt',weights_only=True) if (HERE/f'collect_{variant}_layer_{i:02d}.pt').exists() else {} for i in LAYERS}
    model,meta=e.cr.load('original' if variant=='original' else 'baseline');tok=e.cr.tokenizer()
    if variant=='parent':
        apply_parent(model,e.read_checkpoint('best.pt'))
        save('baseline_hashes.json',{k:tensor_hash(v) for k,v in snapshot(model).items()})
    report['model']=meta;capture=Capture(model,original=variant=='original')
    try:
        for ep in json.loads(INPUTS.read_text())['episodes']:
            if all(ep['id'] in d for d in payloads.values()):continue
            capture.reset();model(input_ids=ids(tok,ep),use_cache=False,logits_to_keep=1)
            for i in LAYERS:
                payloads[str(i)][ep['id']]={'kind':ep['kind'],**capture.values[str(i)]}
                tensor_checkpoint(payloads[str(i)],HERE/f'collect_{variant}_layer_{i:02d}.pt')
            report['input_ids']=[ep_id for ep_id in payloads[str(LAYERS[0])] if all(ep_id in p for p in payloads.values())]
            save(name,report);print('VECTOR_CAPTURE',variant,ep['id'],flush=True)
    finally:capture.close()
    report.update(status='complete',tensor_hashes={str(i):e.cr.file_hash(HERE/f'collect_{variant}_layer_{i:02d}.pt') for i in LAYERS})
    save(name,report);state(status='collected_'+variant,model_process_active=False)

def combined(payload,kind,field):return torch.cat([v[field] for v in payload.values() if v['kind']==kind])

@torch.inference_mode()
def fit_delta(base,language,code,desired):
    _,s,vh=torch.linalg.svd(language,full_matrices=False)
    basis=vh[s>s[0]*1e-5]
    residual=code-(code@basis.T)@basis
    ratio=float(residual.norm()/code.norm())
    info={'preservation_rank':len(basis),'residual_ratio':ratio}
    if ratio<.05:return None,{**info,'abort':'Insufficient residual direction'}
    gram=residual@residual.T;ridge=.01*float(gram.diag().mean())
    coefficient=torch.linalg.solve(gram+ridge*torch.eye(len(code)),desired)
    delta=.25*(residual.T@coefficient).T
    relative=float(delta.norm()/base.float().norm())
    fraction=min(1.,.002/max(relative,1e-20));delta*=fraction
    info.update(ridge=ridge,unclipped_relative_norm=relative,norm_cap_fraction=fraction,
        ideal_relative_norm=float(delta.norm()/base.float().norm()),
        code_fit_relative_residual=float((code@delta.T-.25*fraction*desired).norm()/(.25*fraction*desired).norm().clamp_min(1e-9)),
        ideal_protected_output_norm_max=float((language@delta.T).norm(dim=1).max()))
    return delta,info

@torch.inference_mode()
def construct(model):
    baseline=snapshot(model);expected=json.loads((HERE/'baseline_hashes.json').read_text())
    assert all(tensor_hash(w)==expected[k] for k,w in baseline.items())
    report={'layers':{},'changed_values':{'target':0,'inverse_control':0},'aborted':False}
    manifests={k:{'parent_sha256':PARENT_HASH,'baseline_hashes':expected,'files':{}} for k in ['inverse_control','target']}
    for i in LAYERS:
        key=str(i);own=torch.load(HERE/f'collect_parent_layer_{i:02d}.pt',weights_only=True)
        ref=torch.load(HERE/f'collect_original_layer_{i:02d}.pt',weights_only=True)
        assert set(own)==set(ref)
        for ep in own:assert torch.equal(own[ep]['positions'],ref[ep]['positions'])
        language=combined(own,'ordinary','x');code=combined(own,'coding_prompt','x')
        desired=combined(ref,'coding_prompt','y')-combined(own,'coding_prompt','y')
        delta,info=fit_delta(baseline[key],language,code,desired)
        if delta is None:report.update(aborted=True,abort_layer=i);report['layers'][key]=info;break
        info['variants']={}
        for kind,sign in [('inverse_control',-1),('target',1)]:
            written=(baseline[key].float()+sign*delta).to(baseline[key].dtype)
            actual=written.float()-baseline[key].float();relative=float(actual.norm()/baseline[key].float().norm())
            if relative>.003 or not bool(torch.isfinite(written).all()):report.update(aborted=True,abort_layer=i)
            changed=int((written!=baseline[key]).sum());report['changed_values'][kind]+=changed
            info['variants'][kind]={'actual_relative_norm':relative,'changed_values':changed,
                'rounded_protected_output_norm_max':float((language@actual.T).norm(dim=1).max())}
            path=HERE/f'checkpoints/trial_009_{kind}_layer_{i:02d}.pt'
            tensor_checkpoint({'hypothesis':9,'parent_sha256':PARENT_HASH,'layer':i,
                'baseline_tensor_sha256':expected[key],'weight':written},path)
            manifests[kind]['files'][key]={'path':str(path.relative_to(ROOT)),'sha256':e.cr.file_hash(path)}
        report['layers'][key]=info
    save('construction.json',report)
    if not report['aborted']:
        for kind,m in manifests.items():save(f'patch_{kind}.json',m)
    return report

def patch_weights(kind):
    manifest=json.loads((HERE/f'patch_{kind}.json').read_text());weights={}
    for key,item in manifest['files'].items():
        path=ROOT/item['path'];assert e.cr.file_hash(path)==item['sha256']
        p=torch.load(path,weights_only=True);assert p['parent_sha256']==PARENT_HASH
        assert p['baseline_tensor_sha256']==manifest['baseline_hashes'][key]
        weights[key]=p['weight']
    assert set(weights)=={str(i) for i in LAYERS};return weights

@torch.inference_mode()
def apply(model,parent,baseline,patch=None):
    arch=apply_parent(model,parent)
    for key,w in baseline.items():weight(model,int(key)).copy_(w)
    if patch:
        for key,w in patch.items():
            target=weight(model,int(key));assert target.shape==w.shape and target.dtype==w.dtype and torch.isfinite(w).all()
            target.copy_(w)
    return arch

@torch.inference_mode()
def distance(model,tok):
    capture=Capture(model);sums={str(i):{'code_error':0.,'code_ref_norm':0.,'language_drift':0.,'language_parent_norm':0.} for i in LAYERS}
    refs={str(i):torch.load(HERE/f'collect_original_layer_{i:02d}.pt',weights_only=True) for i in LAYERS}
    parents={str(i):torch.load(HERE/f'collect_parent_layer_{i:02d}.pt',weights_only=True) for i in LAYERS}
    try:
        for ep in json.loads(INPUTS.read_text())['episodes']:
            capture.reset();model(input_ids=ids(tok,ep),use_cache=False,logits_to_keep=1)
            for key,s in sums.items():
                current=capture.values[key]['y'];ref=refs[key][ep['id']]['y'];old=parents[key][ep['id']]['y']
                if ep['kind']=='coding_prompt':s['code_error']+=float((current-ref).square().sum());s['code_ref_norm']+=float(ref.square().sum())
                else:s['language_drift']+=float((current-old).square().sum());s['language_parent_norm']+=float(old.square().sum())
    finally:capture.close()
    return {k:{'relative_code_output_error':(s['code_error']/max(s['code_ref_norm'],1e-9))**.5,
        'relative_language_output_drift':(s['language_drift']/max(s['language_parent_norm'],1e-9))**.5} for k,s in sums.items()}

@torch.inference_mode()
def full(model,tok,kind):
    name=f'full_{kind}.json';p=HERE/name
    d=json.loads(p.read_text()) if p.exists() else {'status':'running','rows':[],'controls':[]}
    historical={r['id']:r for r in json.loads((ROOT/'rsi100/best_metrics.json').read_text())['rows']}
    for task in e.DATA['search']+e.DATA['guard']:
        if task['id'] not in {r['id'] for r in d['rows']}:
            d['rows']+=e.coding(model,tok,[task]);save(name,d)
            if kind=='parent':assert d['rows'][-1]['case_passed']==historical[task['id']]['case_passed']
    for row in e.DATA['search_controls']:
        if row['id'] not in {r['id'] for r in d['controls']}:
            d['controls']+=e.quality(model,tok,[row]);save(name,d)
    d['control_bits']=[r['correct'] for r in d['controls']]
    d['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
    d['status']='complete';save(name,d);return d

@torch.inference_mode()
def trial():
    verify();path=HERE/'trial_009.json'
    d=json.loads(path.read_text()) if path.exists() else {'trial':9,'stage':'constructing','screens':{},'checkpoint_promoted':False,'backward_passes':0}
    if d['stage'] in ['aborted_numerics','rejected_on_screen','rejected_full_gates','eligible_for_validation']:return
    for variant in ['original','parent']:
        c=json.loads((HERE/f'collect_{variant}.json').read_text());assert c['status']=='complete'
        for key,h in c['tensor_hashes'].items():assert e.cr.file_hash(HERE/f'collect_{variant}_layer_{int(key):02d}.pt')==h
    state(status='trial009',model_process_active=True);model,tok,parent,_=load();baseline=snapshot(model)
    if not (HERE/'patch_target.json').exists():construction=construct(model)
    else:construction=json.loads((HERE/'construction.json').read_text())
    if construction['aborted']:
        d.update(stage='aborted_numerics',eligible_for_validation=False,reason='Projection or quantization stability bound failed')
        save(path.name,d);state(status=d['stage'],model_process_active=False);return
    patches={k:patch_weights(k) for k in ['inverse_control','target']}
    saved={r['id']:r for r in json.loads((ROOT/'reasoning/cycle2/trial_006_parent_full.json').read_text())['rows']};prior=[saved[k] for k in SCREEN]
    try:
        for kind in ['inverse_control','target']:
            arch=apply(model,parent,baseline,patches[kind]);r=d['screens'].setdefault(kind,{'rows':[],'architecture':arch})
            if 'internal_distance' not in r:r['internal_distance']=distance(model,tok);save(path.name,d)
            for task in tasks(SCREEN):
                if task['id'] not in {v['id'] for v in r['rows']}:
                    r['rows']+=e.coding(model,tok,[task]);save(path.name,d)
            bits=flatten(r['rows']);old=flatten(prior)
            r.update(case_wins=sum(v and not old[k] for k,v in bits.items()),case_losses=sum(not v and old[k] for k,v in bits.items()))
            save(path.name,d)
        if not dominates(flatten(d['screens']['target']['rows']),flatten(prior)):
            d.update(stage='rejected_on_screen',eligible_for_validation=False,reason='No strict gain with complete case retention')
        else:
            apply(model,parent,baseline);paired=full(model,tok,'parent')
            apply(model,parent,baseline,patches['target']);candidate=full(model,tok,'target')
            ok,reason=accept_paired(candidate,paired,json.loads((ROOT/'rsi100/best_metrics.json').read_text()))
            d.update(stage='eligible_for_validation' if ok else 'rejected_full_gates',eligible_for_validation=ok,reason=reason)
    finally:
        apply(model,parent,baseline);assert all(torch.equal(w,weight(model,int(k))) for k,w in baseline.items())
    save(path.name,d);state(status=d['stage'],model_process_active=False);print('TRIAL009',d['stage'],d['reason'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','original','parent','trial']);a=p.parse_args()
    if a.phase=='freeze':initialize()
    elif a.phase=='trial':trial()
    else:collect(a.phase)
