"""Standalone quality is not draft acceptance; same frozen prompts and budgets."""
import argparse,gc,json,time,torch
from pathlib import Path
from target_model import load_target,tr
from io_parts import load_draft,save_json
from spec_engine import Engine,serial,install_cached_recurrent_rule
from local_cpu.sandbox import evaluate as judge
H=Path(__file__).resolve().parent
@torch.inference_mode()
def main():
 a=argparse.ArgumentParser();a.add_argument('variant',choices=['target','small_initial','small_trained','large_initial','large_trained']);v=a.parse_args().variant;p=H/'reports'/f'quality_{v}.json';r=json.loads(p.read_text()) if p.exists() else {'variant':v,'code':[],'general':[],'scope':'new custom small quality suite, not a standard intelligence benchmark','answers_or_cases_in_prompts':False}
 if r.get('status')=='complete':print('QUALITY_ALREADY_COMPLETE',v);return
 install_cached_recurrent_rule();torch.set_num_threads(4);start=time.perf_counter()
 if v=='target':model,tok,meta=load_target()
 else:
  from transformers import AutoTokenizer
  size,phase=v.split('_');model,meta=load_draft(size,'initial' if phase=='initial' else 'inference');tok=AutoTokenizer.from_pretrained(H.parent/'upstream',local_files_only=True)
 r['model_load_seconds']=time.perf_counter()-start;engine=Engine(model,v)
 for split,budget in [('code',96),('general',32)]:
  rows=json.loads((H/'data'/f'quality_{split}.json').read_text())
  for row in rows:
   if row['id'] in {x['id'] for x in r[split]}:continue
   q=row['prompt'] if split=='code' else row['question'];ids=tok.apply_chat_template([{'role':'user','content':q}],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);out=serial(engine,ids,budget);text=tok.decode(out['ids'],skip_special_tokens=True);out['id']=row['id'];out['text']=text
   if split=='code':out.update(judge(text,row))
   else:out['correct']=tr.e.cr.grade(text,row)[0]
   r[split].append(out);save_json(p,r);print('QUALITY026',v,row['id'],out.get('all_passed',out.get('correct')),flush=True)
 r.update(status='complete',code_tasks=sum(x['all_passed'] for x in r['code']),code_cases=sum(x['passed'] for x in r['code']),code_cases_total=sum(x['total'] for x in r['code']),general_correct=sum(x['correct'] for x in r['general']),metadata=meta);save_json(p,r)
if __name__=='__main__':main()
