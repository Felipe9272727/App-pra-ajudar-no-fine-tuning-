"""Forward-only, jointly distributed RMS-gain calibration; no solution targets."""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import e,torch,load,apply as apply_parent,tasks,PARENT_HASH,tensor_checkpoint
from policy import flatten,dominates,accept_paired
from native_runtime import SOURCE_LAYERS,IDENTITY_LAYERS

ACTIVE=[i for i in range(32) if i not in IDENTITY_LAYERS]
KINDS=['input_layernorm','post_attention_layernorm']
SCREEN=['prefix_sums','rotate_right','longest_run','overlap_count','sum_abs','palindrome','binary_search']
ORDINARY=[
 'Uma observação descreve o que foi visto; uma interpretação tenta explicar por que aconteceu. Uma revisão cuidadosa distingue as duas coisas.',
 'The reader paused at the end of the paragraph and compared its last sentence with the opening statement. The subject had remained the same.',
 'As pessoas organizaram os materiais antes da reunião. Depois, distribuíram as tarefas e anotaram o que ainda precisava de atenção.',
 'A clear description makes assumptions visible and gives another person enough context to understand the question being investigated.',
 'A manhã começou com nuvens baixas sobre a cidade. Ao longo do dia, a luz mudou e as ruas ficaram mais movimentadas.',
 'Several ideas can sound plausible at first. Careful observation helps distinguish a useful explanation from a convenient guess.',
 'Quem escreve para públicos diferentes precisa escolher palavras claras e explicar os termos que podem ser desconhecidos.',
 'The package arrived with a short note describing its contents. The recipient checked the label before putting it on the shelf.',
 'Um resultado inesperado pode revelar uma suposição esquecida. O registro do procedimento permite investigar o que ocorreu.',
 'The conversation returned to the original question after a brief digression. Each participant explained which evidence supported their view.',
 'A pequena oficina guardava ferramentas em caixas identificadas. Ao terminar o trabalho, todos conferiam se o espaço estava organizado.',
 'A reliable record preserves both successful attempts and failed ones, so later decisions can be checked against the original observations.'
]

def save(name,obj):e.cr.atomic_json(HERE/name,obj)
def state(**kw):
    obj=json.loads((HERE/'status.json').read_text());obj.update(kw,updated_unix=time.time());save('status.json',obj)
def norm_module(model,key,original=False):
    index,kind=key.split('.');physical=int(index)
    return getattr(model.model.language_model.layers[SOURCE_LAYERS[physical] if original else physical],kind)
def norm_snapshot(model):return {f'{i}.{kind}':norm_module(model,f'{i}.{kind}').weight.detach().clone() for i in ACTIVE for kind in KINDS}

def verify():
    frozen=json.loads((HERE/'frozen.json').read_text())
    for p,h in frozen['files'].items():assert e.cr.file_hash(ROOT/p)==h,p

def initialize():
    assert len(ACTIVE)==24 and len({SOURCE_LAYERS[i] for i in ACTIVE})==24
    episodes=[{'id':f'ordinary_{i:02d}','kind':'ordinary','input':text} for i,text in enumerate(ORDINARY)]
    episodes += [{'id':t['id'],'kind':'coding_prompt','input':t['prompt']} for t in tasks(SCREEN)]
    save('inputs.json',{'episodes':episodes,'reference_programs_present':False,'golds_present':False})
    names=['reasoning/multi008/PROTOCOL.md','reasoning/multi008/study008.py',
        'reasoning/multi008/validate008.py','reasoning/multi008/inputs.json',
        'reasoning/runtime_helpers.py','rsi100/data.json','rsi100/engine.py','rsi100/policy.py',
        'code_rsi/runtime.py','local_cpu/sandbox.py','v2_adaptation/native_runtime.py',
        'lab_rsi/common.py','upstream/tokenizer_config.json','rsi100/checkpoints/best.pt']
    save('frozen.json',{'files':{p:e.cr.file_hash(ROOT/p) for p in names},
        'eligible_norm_tensors':48,'eligible_scalar_parameters':48*1024,
        'hypothesis':8,'dose_log_bound':.02,'damping':.25,'actual_gain_change_bound':.03,
        'quality_outputs_observed':False,'heldout_observed':False})

class Moments:
    def __init__(self,model,original=False):
        self.model=model;self.original=original;self.sums={};self.counts={};self.handles=[]
        for physical in ACTIVE:
            for kind in KINDS:
                key=f'{physical}.{kind}'
                def capture(module,inputs,output,key=key,physical=physical):
                    assert torch.isfinite(output).all(),key
                    layer=self.model.model.language_model.layers[physical] if not self.original else None
                    visit=int(layer._last_native_visit) if layer is not None and 4<=physical<28 else 0
                    tag=(key,visit);x=output.detach().float().reshape(-1,output.shape[-1])
                    value=x.square().sum(0)
                    self.sums[tag]=self.sums.get(tag,torch.zeros_like(value))+value
                    self.counts[tag]=self.counts.get(tag,0)+len(x)
                self.handles.append(norm_module(model,key,original).register_forward_hook(capture))
    def reset(self):self.sums={};self.counts={}
    def finish(self):
        moments={};visits={}
        for key in [f'{i}.{k}' for i in ACTIVE for k in KINDS]:
            physical=int(key.split('.')[0]);weighted=None;denom=0.
            for tag,total in self.sums.items():
                if tag[0]!=key:continue
                v=tag[1];gain=float(self.model.model.language_model.layers[physical].native_visit_gain[v]) if not self.original and 4<=physical<28 else 1.
                weighted=total*gain if weighted is None else weighted+total*gain
                denom+=self.counts[tag]*gain
                visits[f'{key}:visit{v}']={'positions':self.counts[tag],'weight':gain,
                    'rms':float((total/self.counts[tag]).mean().sqrt())}
            assert weighted is not None and denom>0,key
            moments[key]=weighted/denom
        return {'moments':moments,'visit_statistics':visits}
    def close(self):
        for handle in self.handles:handle.remove()

def input_ids(tok,episode):
    if episode['kind']=='coding_prompt':return e.cr.prompt(tok,episode['input'])
    return tok(episode['input'],return_tensors='pt',add_special_tokens=False)['input_ids']

@torch.inference_mode()
def collect(variant):
    verify();path=HERE/f'collect_{variant}.json';tp=HERE/f'collect_{variant}.pt'
    report=json.loads(path.read_text()) if path.exists() else {'variant':variant,'status':'running','prefill_ids':[],'decoding_rows':[],
        'no_reference_solution_used':True,'reference_model_generates_solutions':False}
    if report['status']=='complete':return
    state(status='collecting_'+variant,model_process_active=True)
    payload=torch.load(tp,weights_only=True) if tp.exists() else {'prefill':{},'decoding':{}}
    model,meta=e.cr.load('original' if variant=='original' else 'baseline');tok=e.cr.tokenizer()
    if variant=='parent':
        parent=e.read_checkpoint('best.pt');meta['architecture']=apply_parent(model,parent)
        baseline=norm_snapshot(model);basepath=HERE/'checkpoints/baseline_norms.pt'
        if basepath.exists():
            saved=torch.load(basepath,weights_only=True);assert all(torch.equal(v,saved[k]) for k,v in baseline.items())
        else:tensor_checkpoint(baseline,basepath)
    report['model']=meta;collector=Moments(model,original=variant=='original')
    episodes=json.loads((HERE/'inputs.json').read_text())['episodes']
    try:
        for ep in episodes:
            if ep['id'] in payload['prefill']:continue
            collector.reset();ids=input_ids(tok,ep)
            model(input_ids=ids,use_cache=False,logits_to_keep=1)
            payload['prefill'][ep['id']]=collector.finish()
            tensor_checkpoint(payload,tp)
            report['prefill_ids']=list(payload['prefill']);save(path.name,report)
            print('PREFILL_MOMENT',variant,ep['id'],ids.shape[1],flush=True)
        if variant=='parent':
            prior={r['id']:r for r in json.loads((ROOT/'reasoning/cycle2/trial_006_parent_full.json').read_text())['rows']}
            for task in tasks(SCREEN):
                if task['id'] in payload['decoding']:continue
                collector.reset();generated=e.cr.generate(model,tok,task['prompt']);generated.pop('trace')
                assert generated['output']==prior[task['id']]['output'],'Unexpected parent drift before editing'
                payload['decoding'][task['id']]=collector.finish();tensor_checkpoint(payload,tp)
                report['decoding_rows'].append({'id':task['id'],**generated,
                    'matches_saved_parent_text':True,'reference_passed_cases':prior[task['id']]['passed'],
                    'reference_total_cases':prior[task['id']]['total']})
                save(path.name,report);print('NEW_DECODING_MOMENTS',task['id'],generated['new_tokens'],flush=True)
    finally:collector.close()
    report['status']='complete';report['tensor_sha256']=e.cr.file_hash(tp);save(path.name,report)
    state(status='collected_'+variant,model_process_active=False)

def aggregate(episodes):
    return {k:torch.stack([x['moments'][k] for x in episodes.values()]).mean(0) for k in next(iter(episodes.values()))['moments']}

def corrected_vector(w,log_scale):
    g=1+w.float();new=(g*log_scale.exp()-1).to(w.dtype)
    ratio=torch.where(g.abs()>1e-6,(1+new.float())/g,torch.ones_like(g))
    bad=(ratio-1).abs()>.03
    bad|=(g.abs()<=1e-6)|~torch.isfinite(new)|(g*(1+new.float())<0)
    unchanged=(log_scale==0)|((1+new.float())==g)
    return torch.where(bad|unchanged,w,new),bad

@torch.inference_mode()
def construct():
    ref=aggregate(torch.load(HERE/'collect_original.pt',weights_only=True)['prefill'])
    own=aggregate(torch.load(HERE/'collect_parent.pt',weights_only=True)['prefill'])
    baseline=torch.load(HERE/'checkpoints/baseline_norms.pt',weights_only=True)
    patches={};diagnostic={'per_tensor':{},'actual_changes':{}}
    z={}
    for key in ref:
        value=.25*.5*((ref[key]+1e-6).log()-(own[key]+1e-6).log())
        value=value-value.mean();z[key]=value.clamp(-.02,.02)
        diagnostic['per_tensor'][key]={'prefill_relative_rms_deviation':float((own[key].sqrt()-ref[key].sqrt()).norm()/ref[key].sqrt().norm()),
            'mean_abs_log_correction':float(z[key].abs().mean()),'clipped_coordinates':int((value.abs()>.02).sum())}
    for kind,sign in [('inverse_control',-1),('target',1)]:
        written={};changes={}
        for key,w in baseline.items():
            g=1+w.float();new,bad=corrected_vector(w,sign*z[key]);assert torch.isfinite(new).all()
            written[key]=new
            changes[key]={'changed_values':int((new!=w).sum()),'constraints_reverted':int(bad.sum()),
                'actual_max_relative_gain_change':float(torch.where(g.abs()>1e-6,((1+new.float())/g-1).abs(),torch.zeros_like(g)).max())}
        patch={'hypothesis':8,'kind':kind,'parent_sha256':PARENT_HASH,
            'baseline_norms_sha256':e.cr.file_hash(HERE/'checkpoints/baseline_norms.pt'),'norm_weights':written}
        tensor_checkpoint(patch,HERE/f'checkpoints/trial_008_{kind}.pt');patches[kind]=patch
        diagnostic['actual_changes'][kind]={'per_tensor':changes,'changed_tensors':sum(x['changed_values']>0 for x in changes.values()),
            'changed_values':sum(x['changed_values'] for x in changes.values())}
    tensor_checkpoint({'log_corrections':z,'reference_moments':ref,'parent_moments':own},HERE/'directions_008.pt')
    save('construction.json',diagnostic);return patches

@torch.inference_mode()
def apply(model,parent,baseline,patch=None):
    arch=apply_parent(model,parent)
    for key,w in baseline.items():norm_module(model,key).weight.copy_(w)
    if patch:
        assert patch['parent_sha256']==PARENT_HASH
        assert set(patch['norm_weights'])==set(baseline) and len(baseline)==48
        assert patch['baseline_norms_sha256']==e.cr.file_hash(HERE/'checkpoints/baseline_norms.pt')
        for key,w in patch['norm_weights'].items():
            target=norm_module(model,key).weight
            assert target.shape==w.shape and target.dtype==w.dtype and torch.isfinite(w).all()
            target.copy_(w)
    return arch

@torch.inference_mode()
def actual_moment_distance(model,tok):
    collector=Moments(model);episodes={}
    try:
        for ep in json.loads((HERE/'inputs.json').read_text())['episodes']:
            collector.reset();model(input_ids=input_ids(tok,ep),use_cache=False,logits_to_keep=1)
            episodes[ep['id']]=collector.finish()
    finally:collector.close()
    measured=aggregate(episodes)
    ref=torch.load(HERE/'directions_008.pt',weights_only=True)['reference_moments']
    errors={k:float(((measured[k]+1e-6).log()-(ref[k]+1e-6).log()).square().mean()) for k in ref}
    return {'mean_squared_log_moment_distance':sum(errors.values())/len(errors),'per_tensor':errors}

@torch.inference_mode()
def full(model,tok,kind):
    path=HERE/f'full_{kind}.json'
    report=json.loads(path.read_text()) if path.exists() else {'rows':[],'controls':[],'status':'running'}
    prior={r['id']:r for r in json.loads((ROOT/'rsi100/best_metrics.json').read_text())['rows']}
    for task in e.DATA['search']+e.DATA['guard']:
        if task['id'] in {r['id'] for r in report['rows']}:continue
        report['rows']+=e.coding(model,tok,[task])
        if kind=='parent':assert report['rows'][-1]['case_passed']==prior[task['id']]['case_passed'],'Parent case drift'
        save(path.name,report)
    for row in e.DATA['search_controls']:
        if row['id'] not in {r['id'] for r in report['controls']}:
            report['controls']+=e.quality(model,tok,[row]);save(path.name,report)
    report['control_bits']=[x['correct'] for x in report['controls']]
    report['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
    report['status']='complete';save(path.name,report);return report

@torch.inference_mode()
def trial():
    verify();path=HERE/'trial_008.json'
    report=json.loads(path.read_text()) if path.exists() else {'trial':8,'stage':'constructing','screens':{},
        'checkpoint_promoted':False,'backward_passes':0,'parent_sha256':PARENT_HASH}
    if report['stage'] in ['rejected_on_screen','rejected_full_gates','eligible_for_validation']:return
    for v in ['original','parent']:
        collected=json.loads((HERE/f'collect_{v}.json').read_text())
        assert collected['status']=='complete'
        assert collected['tensor_sha256']==e.cr.file_hash(HERE/f'collect_{v}.pt')
    if not (HERE/'checkpoints/trial_008_target.pt').exists():patches=construct()
    else:patches={k:torch.load(HERE/f'checkpoints/trial_008_{k}.pt',weights_only=True) for k in ['inverse_control','target']}
    report['patch_hashes']={k:e.cr.file_hash(HERE/f'checkpoints/trial_008_{k}.pt') for k in patches}
    save(path.name,report);state(status='trial008',model_process_active=True)
    model,tok,parent,_=load();baseline=torch.load(HERE/'checkpoints/baseline_norms.pt',weights_only=True)
    assert all(torch.equal(v,norm_snapshot(model)[k]) for k,v in baseline.items())
    reference={r['id']:r for r in json.loads((ROOT/'reasoning/cycle2/trial_006_parent_full.json').read_text())['rows']}
    prior=[reference[k] for k in SCREEN]
    try:
        for kind in ['inverse_control','target']:
            arch=apply(model,parent,baseline,patches[kind])
            result=report['screens'].setdefault(kind,{'rows':[],'architecture':arch})
            if 'moments' not in result:result['moments']=actual_moment_distance(model,tok);save(path.name,report)
            for task in tasks(SCREEN):
                if task['id'] not in {r['id'] for r in result['rows']}:
                    result['rows']+=e.coding(model,tok,[task]);save(path.name,report)
            bits=flatten(result['rows']);old=flatten(prior)
            result.update(case_wins=sum(v and not old[k] for k,v in bits.items()),case_losses=sum(not v and old[k] for k,v in bits.items()))
            save(path.name,report)
        if not dominates(flatten(report['screens']['target']['rows']),flatten(prior)):
            report.update(stage='rejected_on_screen',eligible_for_validation=False,reason='No strict case gain with complete screen retention')
        else:
            apply(model,parent,baseline);paired=full(model,tok,'parent')
            apply(model,parent,baseline,patches['target']);candidate=full(model,tok,'target')
            accepted,reason=accept_paired(candidate,paired,json.loads((ROOT/'rsi100/best_metrics.json').read_text()))
            report.update(stage='eligible_for_validation' if accepted else 'rejected_full_gates',eligible_for_validation=accepted,reason=reason)
    finally:
        apply(model,parent,baseline)
        assert all(torch.equal(v,norm_snapshot(model)[k]) for k,v in baseline.items()),'Incomplete norm rollback'
    save(path.name,report);state(status=report['stage'],model_process_active=False)
    print('TRIAL008',report['stage'],report['reason'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','original','parent','trial']);a=p.parse_args()
    if a.phase=='freeze':initialize()
    elif a.phase=='trial':trial()
    else:collect(a.phase)
