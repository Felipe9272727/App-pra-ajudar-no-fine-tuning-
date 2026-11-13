"""Live engineering preflight on non-benchmark inputs and a seeded untrained child."""
import gc,hashlib,json,torch
from pathlib import Path
from target_model import load_target,tr
from draft_model import DraftLM
from spec_engine import Engine,serial,speculative,install_cached_recurrent_rule
from io_parts import save_json
H=Path(__file__).resolve().parent

def fingerprint(cache):
 h=hashlib.sha256()
 for i,l in enumerate(cache.layers):
  for name,v in sorted(vars(l).items()):
   if torch.is_tensor(v):h.update(str((i,name,tuple(v.shape),str(v.dtype))).encode());h.update(v.detach().contiguous().view(torch.uint8).numpy().tobytes())
   elif isinstance(v,(int,float,bool,str)):h.update(str((i,name,v)).encode())
 h.update(str(getattr(cache,'_loop_execution_plan',None)).encode());return h.hexdigest()
@torch.inference_mode()
def main():
 install_cached_recurrent_rule();target,tok,meta=load_target();draft=DraftLM('small',20261113).inference_bf16();t=Engine(target,'target');d=Engine(draft,'seeded-small');rows=[]
 for q in ['Hi.','Write Python function f(x) that returns x plus one. Return only code.']:
  p=tok.apply_chat_template([{'role':'user','content':q}],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);r=serial(t,p,12);s=speculative(t,d,p,12,4);safe=speculative(t,d,p,12,4,verify_mode='serial');assert safe['ids']==r['ids'],'Serial verification must preserve target output';rows.append({'prompt':q,'serial_ids':r['ids'],'block_ids':s['ids'],'serial_verified_ids':safe['ids'],'block_matches_serial':r['ids']==s['ids'],'serial_verification_matches':True,'untrained_child_not_quality_scored':True,'block_proposed':s['proposed'],'block_accepted':s['accepted']})
 _,c=t.forward(p);f=fingerprint(c);clone=t.clone(c);assert fingerprint(clone)==f;_,changed=t.forward([12],clone);assert fingerprint(c)==f,'Snapshot aliasing corrupted prefix';assert fingerprint(changed)!=f;assert len(c.layers)==56
 save_json(H/'reports/cache_preflight.json',{'rows':rows,'block_greedy_parity':all(x['block_matches_serial'] for x in rows),'snapshot_deepcopy_independent':True,'snapshot_restoration_exact':True,'virtual_slots':len(c.layers),'no_speed_or_quality_claim':True});print('CACHE_PREFLIGHT_COMPLETE',all(x['block_matches_serial'] for x in rows),flush=True)
if __name__=='__main__':main()
