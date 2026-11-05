"""Real loop drift, causal cached replay and language comparison."""
import argparse,hashlib,statistics,time,copy,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from loop012.core import *

@torch.inference_mode()
def initialize():
 assert not (HERE/'frozen.json').exists()
 files=['loop012/PROTOCOL.md','loop012/style_inputs.json','loop012/core.py','loop012/diagnose.py','loop012/edit.py',
 'diagnostic011/capture_complete.json','diagnostic011/token_integrity.json','reasoning/cycle2/development_original.json',
 'reasoning/cycle2/trial_006_parent_full.json','reasoning/multi008/inputs.json','reasoning/runtime_helpers.py',
 'v2_adaptation/native_runtime.py','modeling_sensenova_loop.py','rsi100/checkpoints/best.pt','rsi100/data.json',
 'code_rsi/runtime.py','local_cpu/sandbox.py']
 save('frozen.json',{'files':{p:e.cr.file_hash(ROOT/p) for p in files},'new_quality_outputs_observed':False,'no_style_inputs_in_construction':True})
 state('registered_not_started')

@torch.inference_mode()
def drift():
 verify();rows=[];layers={i:[] for i in range(4,28)}
 for task in SCREEN:
  p=torch.load(ROOT/'diagnostic011/activations'/f'{task}.pt',weights_only=True)
  for step,snap in p['snapshots'].items():
   record={'id':task,'step':step,'layers':{}}
   for i in range(4,28):
    key=f'model.language_model.layers.{i}'
    a=snap[(key,0)]['output'].float().flatten();b=snap[(key,1)]['output'].float().flatten()
    d={'relative_l2':float((b-a).norm()/a.norm().clamp_min(1e-12)),'cosine':float(torch.nn.functional.cosine_similarity(a,b,dim=0)),'max_abs_delta':float((b-a).abs().max()),'bitwise_equal':bool(torch.equal(a,b))}
    record['layers'][str(i)]=d;layers[i].append(d)
   rows.append(record)
 summary={str(i):{'mean_relative_l2':statistics.mean(x['relative_l2'] for x in v),'mean_cosine':statistics.mean(x['cosine'] for x in v),'equal_points':sum(x['bitwise_equal'] for x in v),'points':len(v)} for i,v in layers.items()}
 save('loop_drift.json',{'status':'complete','rows':rows,'by_physical_layer':summary,'loop_exit_layer':27,'causal_quality_gain_established':False})
 print('LOOP_EXIT_DRIFT',summary['27'],flush=True)

@torch.inference_mode()
def bypass():
 verify();assert not (HERE/'bypass_code.json').exists();state('loop_bypass_code',True)
 m,t,p,meta=load();report={'status':'running','rows':[],'kind':'diagnostic output replacement, not a weight candidate','architecture':e.cr.check_architecture(m,2)}
 try:
  with BypassSecond(m) as bypass:
   for task in tasks(SCREEN):report['rows']+=e.coding(m,t,[task]);save('bypass_code.json',report)
   report['second_exits_replaced']=bypass.calls
 finally:state('loop_bypass_code_stopped')
 base={r['id']:r for r in parent_rows()};report['comparisons']={r['id']:{'same_output':r['output']==base[r['id']]['output'],'baseline_cases':base[r['id']]['passed'],'bypass_cases':r['passed'],'baseline_complete':base[r['id']]['all_passed'],'bypass_complete':r['all_passed']} for r in report['rows']}
 report.update(status='complete',cases_passed=sum(r['passed'] for r in report['rows']),tasks_passed=sum(r['all_passed'] for r in report['rows']));save('bypass_code.json',report)

@torch.inference_mode()
def cached():
 verify();assert not (HERE/'cached_loop.json').exists();state('cached_loop_causality',True)
 m,t,p,meta=load();report={'status':'running','rows':[],'method':'copy cache before original HF-generate decision, replay identical cached call'}
 for task in tasks(SCREEN):
  old=torch.load(ROOT/'diagnostic011/activations'/f"{task['id']}.pt",weights_only=True);step=old['suspected_point']['actual_token_index'];assert step is not None
  box={};counter=[-1]
  def pre(module,args,kwargs):
   counter[0]+=1
   if counter[0]==step:box['args']=copy.deepcopy(args);box['kwargs']=copy.deepcopy(kwargs)
  def post(module,args,kwargs,out):
   if counter[0]==step:box['logits']=out.logits[0,-1].detach().clone()
  a=m.register_forward_pre_hook(pre,with_kwargs=True);b=m.register_forward_hook(post,with_kwargs=True)
  try:
   ids=e.cr.prompt(t,task['prompt']);generated=m.generate(input_ids=ids,max_new_tokens=step+1,use_cache=True,do_sample=False,pad_token_id=t.eos_token_id)
  finally:a.remove();b.remove()
  own=generated[0,ids.shape[1]:];assert torch.equal(own,old['own_generated_token_ids'][:step+1])
  normal=m(*copy.deepcopy(box['args']),**copy.deepcopy(box['kwargs'])).logits[0,-1].float();expected=box['logits'].float()
  replay_delta=float((normal-expected).abs().max());assert replay_delta<=1e-6,(task['id'],replay_delta)
  with BypassSecond(m):alternative=m(*copy.deepcopy(box['args']),**copy.deepcopy(box['kwargs'])).logits[0,-1].float()
  prob=normal.softmax(0);kl=float((prob*(normal.log_softmax(0)-alternative.log_softmax(0))).sum())
  row={'id':task['id'],'step':step,'cache_replay_max_abs_difference':replay_delta,'baseline_top_token':int(normal.argmax()),'bypass_top_token':int(alternative.argmax()),'argmax_changed':bool(normal.argmax()!=alternative.argmax()),'max_logit_change':float((alternative-normal).abs().max()),'kl_parent_to_bypass':kl,'original_token':int(own[-1])}
  report['rows'].append(row);save('cached_loop.json',report);print('CACHED_LOOP',row,flush=True)
 report['status']='complete';save('cached_loop.json',report);state('cached_loop_complete')

@torch.inference_mode()
def style(kind):
 verify();path=HERE/f'style_{kind}.json';assert not path.exists();state('style_'+kind,True)
 m,t,meta=load_variant('parent' if kind=='bypass' else kind);report={'status':'running','variant':kind,'model':meta,'rows':[]}
 context=BypassSecond(m) if kind=='bypass' else None
 if context:context.__enter__()
 try:
  for row in json.loads((HERE/'style_inputs.json').read_text())['rows']:
   if kind=='bypass' and row['id'] not in ['explain_cache_pt','uncertainty_pt','summary_pt']:continue
   out=e.cr.generate(m,t,row['prompt'],max_tokens=128);out.pop('trace');report['rows'].append({'id':row['id'],**out,'metrics':style_metrics(out['output'],row['id'])});save(path.name,report);print('STYLE',kind,row['id'],out['new_tokens'],flush=True)
 finally:
  if context:context.__exit__()
 report['status']='complete';save(path.name,report);state('style_'+kind+'_complete')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['initialize','drift','bypass','cached','style']);p.add_argument('variant',nargs='?');a=p.parse_args()
 if a.phase=='style':style(a.variant)
 else:globals()[a.phase]()
