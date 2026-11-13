"""Collect actual teacher behavior only on declared TRAIN questions, no gold solutions."""
import hashlib,json,time
from pathlib import Path
from target_model import load_target,tr
from spec_engine import Engine,serial,install_cached_recurrent_rule
from io_parts import save_json
H=Path(__file__).resolve().parent
@tr.torch.inference_mode()
def main():
 path=H/'data/teacher_traces.json';rows=json.loads(path.read_text()) if path.exists() else [];qs=json.loads((H/'data/teacher_prompts.json').read_text())
 if len(rows)==len(qs):print('TEACHER_ALREADY_COMPLETE');return
 model,tok,meta=load_target();install_cached_recurrent_rule();engine=Engine(model,'target')
 for q in qs:
  if q['id'] in {x['id'] for x in rows}:continue
  ids=tok.apply_chat_template([{'role':'user','content':q['prompt']}],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);r=serial(engine,ids,48);rows.append({'id':q['id'],'prompt':q['prompt'],'prompt_ids':ids,'answer_ids':r['ids'],'answer_text':tok.decode(r['ids'],skip_special_tokens=True),'truncated':len(r['ids'])==48 and r['ids'][-1] not in [248044,248046],'seconds':r['seconds'],'teacher_parent_sha256':tr.PARENT_HASH,'behavior_trace_not_verified_solution':True});save_json(path,rows);print('TEACHER026',q['id'],len(r['ids']),flush=True)
 save_json(H/'reports/teacher_collection.json',{'completed':len(rows),'teacher_unchanged':True,'parent_sha256':tr.PARENT_HASH,'solutions_provided_to_teacher':False,'quality_or_speed_prompts_queried':False})
if __name__=='__main__':main()
