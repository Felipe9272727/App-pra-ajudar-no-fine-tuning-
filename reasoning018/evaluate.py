"""Unchanged historical controls; paired observed thinking teaching diagnostics."""
import gc,json,sys,time,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reasoning018';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
from reasoning018.restore import load_candidate
from local_cpu.sandbox import evaluate as judge

def save(n,v):tr.e.cr.atomic_json(HERE/n,v)
@tr.torch.inference_mode()
def main():
 a=argparse.ArgumentParser();a.add_argument('variant',choices=['parent','candidate']);args=a.parse_args()
 path=HERE/('evaluation_'+args.variant+'.json');report=json.loads(path.read_text()) if path.exists() else {'variant':args.variant,'protocol':{'controls_thinking':False,'code_thinking':True,'greedy':True,'seed':0,'control_budget':64,'code_budget':256,'threads':4,'answers_in_generation_inputs':False,'cases_in_generation_inputs':False,'observed_teaching_diagnostic_not_fresh':True},'controls':[],'code':[]}
 assert report.get('status')!='complete','Do not repeat completed run'
 if args.variant=='candidate':model,tok,meta,audit=load_candidate();report['checkpoint_sha256']=audit['checkpoint_sha256']
 else:model,tok,parent,meta=tr.load();del parent
 controls=json.loads((ROOT/'review013/controls.json').read_text())
 if args.variant=='candidate':
  for row in controls:
   if row['id'] in {x['id'] for x in report['controls']}:continue
   out=tr.e.cr.generate(model,tok,row['question'],max_tokens=64,thinking=False);out.pop('trace',None);out['correct']=tr.e.cr.grade(out['output'],row)[0];report['controls'].append({'id':row['id'],**out});save(path.name,report);print('EVAL018',args.variant,'control',row['id'],out['correct'],flush=True)
 else:
  # Parent hashes and protocol are unchanged; reuse completed matching controls.
  old=json.loads((ROOT/'review013/controls_parent.json').read_text());report['controls']=old['rows'];report['controls_reused_source']='review013/controls_parent.json';report['controls_reused_matching_weight_hash']=tr.PARENT_HASH
 for id in ['above_0','prefix_offset_0']:
  if id in {x['id'] for x in report['code']}:continue
  row=next(x for x in json.loads((HERE/'code_train.json').read_text()) if x['id']==id)
  ids=tr.e.cr.prompt(tok,row['prompt'],thinking=True);tr.torch.manual_seed(0);start=time.monotonic()
  outputs=model.generate(input_ids=ids,max_new_tokens=256,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id)[0,ids.shape[1]:]
  raw=tok.decode(outputs,skip_special_tokens=True);closed='</think>' in raw;final=raw.rsplit('</think>',1)[-1].strip() if closed else ''
  score=judge(final,row);entry={'id':id,'final_output':final,'thinking_closed':closed,'has_final':bool(final),'new_tokens':len(outputs),'hit_limit':len(outputs)==256,'raw_output_sha256':hashlib.sha256(raw.encode()).hexdigest(),'seconds':time.monotonic()-start,**score};report['code'].append(entry);save(path.name,report);print('EVAL018',args.variant,'code',id,entry['all_passed'],entry['new_tokens'],entry['thinking_closed'],flush=True)
 report.update(status='complete',controls_correct=sum(r['correct'] for r in report['controls']),code_tasks_passed=sum(r['all_passed'] and r['has_final'] for r in report['code']),code_cases_passed=sum(r['passed'] for r in report['code']),code_cases_total=sum(r['total'] for r in report['code']));save(path.name,report)
if __name__=='__main__':main()
