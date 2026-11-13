"""Frozen old source015E8program/12control retention for the new adapter."""
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse022';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
from tooluse022.train import torch,tr,load_e,verify
from tooluse022.evaluate import adapter
from supervised014.judge import evaluate as judge
@torch.inference_mode()
def main():
 verify();model,tok,meta=load_e();handle=adapter(model)
 for role,path,budget in [('controls','review013/controls.json',64),('taught','supervised015/attempt_e/train.json',320)]:
  dst=HERE/'results'/('retention_'+role+'.json');results=json.loads(dst.read_text()) if dst.exists() else [];rows=json.loads((ROOT/path).read_text())
  old=json.loads((ROOT/'supervised015/attempt_e'/('controls_specialist.json' if role=='controls' else 'target_specialist.json')).read_text());old={r['id']:r for r in old['rows']}
  for row in rows:
   if any(r['id']==row['id'] for r in results):continue
   question=row['question'] if role=='controls' else row['prompt'];out=tr.e.cr.generate(model,tok,question,max_tokens=budget);out.pop('trace',None)
   score={'correct':tr.e.cr.grade(out['output'],row)[0]} if role=='controls' else judge(out['output'],row)
   result={'id':row['id'],**out,**score,'parent_correct':old[row['id']].get('correct',old[row['id']].get('all_passed')),'parent_output':old[row['id']]['output'],'scope':'sourcePyTorch raw, user-only, no tool system/runtime'};results.append(result);tr.e.cr.atomic_json(dst,results);print('RETENTION',role,row['id'],score.get('correct',score.get('all_passed')),flush=True)
 handle.remove()
if __name__=='__main__':main()
