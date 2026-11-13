"""Matched free generation across original, general parent and every epoch."""
import argparse,gc,time
from common import *
from local_cpu.sandbox import evaluate as judge

@torch.inference_mode()
def generate(model,tok,question,budget,bypass=False,probe=False):
 ids=tr.e.cr.prompt(tok,question,thinking=False);torch.manual_seed(0);hook=None;states=[];first=[None];layer=getattr(model.model,'language_model',None)
 if layer is not None and len(layer.layers)==32 and (probe or bypass):
  block=layer.layers[27]
  def capture(m,args,out):
   visit=m._last_native_visit
   if visit==0:first[0]=out.detach().clone()
   elif visit==1:
    if out.shape[1]>1 and first[0] is not None:
     a=first[0][0,-1].float().flatten();b=out[0,-1].float().flatten();states.append({'relative_L2':float((b-a).norm()/a.norm().clamp_min(1e-12)),'cosine':float(torch.nn.functional.cosine_similarity(a,b,dim=0)),'first_norm':float(a.norm()),'second_norm':float(b.norm())})
    if bypass:return first[0]
  hook=block.register_forward_hook(capture)
 start=time.monotonic()
 try:out=model.generate(input_ids=ids,max_new_tokens=budget,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id,eos_token_id=[248044,248046])[0,ids.shape[1]:]
 finally:
  if hook:hook.remove()
 ended=bool(len(out)) and int(out[-1]) in [248044,248046];return {'output':tok.decode(out,skip_special_tokens=True),'new_tokens':len(out),'hit_limit':len(out)==budget and not ended,'ended_eos':ended,'seconds_descriptive_only':time.monotonic()-start,'loop_exit_prefill':states,'second_contribution_bypassed':bypass,'all56_layer_executions_retained_if_hybrid':True}

def run(variant,phase='development',bypass=False):
 verify();suffix='_bypass' if bypass else '';name=f'reports/{phase}_{variant}{suffix}.json';p=HERE/name
 report=read(name) if p.exists() else {'variant':variant,'phase':phase,'controls':[],'code':[],'protocol':{'thinking':False,'greedy':True,'seed':0,'threads':4,'code_budget':160,'control_budget':64,'eos_ids':[248044,248046],'reference_answers_or_tests_in_generation_inputs':False,'framework':'PyTorch CPU BF16 eager','bypass_diagnostic_only':bypass}}
 if report.get('status')=='complete':print('SKIP_COMPLETED',name,flush=True);return
 model,tok,meta=load_variant(variant);report['source_metadata']=meta
 if phase=='development':
  controls=json.loads((ROOT/'review013/controls.json').read_text()) if not bypass else []
  code=[{**r,'evaluation_split':'taught_fit'} for r in read('code_train.json') if r['id'] in ['above_0','prefix_offset_0']]
  if not bypass:code += [{**r,'evaluation_split':'validation'} for r in read('validation.json')]
 else:
  assert read('selection.json').get('selected_epoch') is not None,'Final gate remains closed';controls=read('final_general.json');code=[{**r,'evaluation_split':'final'} for r in read('final.json')]
 for row in controls:
  if row['id'] in {r['id'] for r in report['controls']}:continue
  r=generate(model,tok,row['question'],64);r['id']=row['id'];r['correct']=tr.e.cr.grade(r['output'],row)[0];report['controls'].append(r);save(name,report);print('CONTROL025',variant,row['id'],r['correct'],flush=True)
 for row in code:
  if row['id'] in {r['id'] for r in report['code']}:continue
  r=generate(model,tok,row['prompt'],160,bypass=bypass,probe=not bypass);score=judge(r['output'],row);report['code'].append({'id':row['id'],'split':row['evaluation_split'],**r,**score});save(name,report);print('CODE025',phase,variant,row['id'],score['passed'],score['total'],flush=True)
 report.update(status='complete',controls_correct=sum(r['correct'] for r in report['controls']),taught_tasks_passed=sum(r['all_passed'] for r in report['code'] if r['split']=='taught_fit'),validation_tasks_passed=sum(r['all_passed'] for r in report['code'] if r['split']=='validation'),final_tasks_passed=sum(r['all_passed'] for r in report['code'] if r['split']=='final'));save(name,report);del model;gc.collect();print('EVAL025_COMPLETE',name,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('variant',choices=['original','parent','epoch1','epoch2','epoch3']);p.add_argument('--phase',default='development',choices=['development','final']);p.add_argument('--bypass',action='store_true');a=p.parse_args();run(a.variant,a.phase,a.bypass)
