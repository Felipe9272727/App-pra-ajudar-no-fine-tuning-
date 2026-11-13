"""Paired and historical general/control/coding retention, unchanged old judges."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse023';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
from tooluse023.train import torch,tr,load_general,verify
from tooluse023.evaluate import apply_candidate
@torch.inference_mode()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('variant',choices=['parent','candidate']);a=ap.parse_args();verify();model,tok,meta=load_general()
 if a.variant=='candidate':apply_candidate(model)
 bank=json.loads((ROOT/'rsi100/data.json').read_text());coding=bank['search']+bank['guard'];old={r['id']:r for r in json.loads((ROOT/'rsi100/best_metrics.json').read_text())['rows']}
 for role,rows,budget in [('controls',json.loads((ROOT/'review013/controls.json').read_text()),64),('coding',coding,160)]:
  p=HERE/'results'/f'retention_{role}_{a.variant}.json';out=json.loads(p.read_text()) if p.exists() else []
  for row in rows:
   if any(r['id']==row['id'] for r in out):continue
   question=row['question'] if role=='controls' else row['prompt'];result=tr.e.cr.generate(model,tok,question,max_tokens=budget);result.pop('trace',None);score={'correct':tr.e.cr.grade(result['output'],row)[0]} if role=='controls' else tr.e.cr.evaluate(result['output'],row);entry={'id':row['id'],**result,**score}
   if role=='coding':entry['historical_parent_case_passed']=old[row['id']]['case_passed']
   out.append(entry);tr.e.cr.atomic_json(p,out);print('RETENTION',a.variant,role,row['id'],score.get('correct',score.get('all_passed')),flush=True)
if __name__=='__main__':main()
