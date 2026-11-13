"""Frozen parity and fixed paired end-to-end resident-model CPU timings."""
import copy,gc,json,statistics,time,torch
from pathlib import Path
from target_model import load_target
from io_parts import load_draft,save_json
from spec_engine import Engine,serial,speculative,install_cached_recurrent_rule
H=Path(__file__).resolve().parent
@torch.inference_mode()
def main():
 cfg=json.loads((H/'config.json').read_text());report=H/'reports/timing_rows.json';assert not report.exists(),'Do not repeat timing; reconcile saved partial state first';install_cached_recurrent_rule();torch.set_num_threads(4);start=time.perf_counter();model,tok,meta=load_target();small,_=load_draft('small');large,_=load_draft('large');loads=time.perf_counter()-start;t=Engine(model,'target');children={'small':Engine(small,'small'),'large':Engine(large,'large')};qs=json.loads((H/'data/speed_prompts.json').read_text());parity=[];references={};modes={}
 def run(question,size=None,budget=32,mode='block'):
  begin=time.perf_counter();p=tok.apply_chat_template([{'role':'user','content':question}],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);tokenize=time.perf_counter()-begin;r=serial(t,p,budget) if size is None else speculative(t,children[size],p,budget,4,verify_mode=mode);r['text']=tok.decode(r['ids'],skip_special_tokens=True);r['resident_request_seconds']=time.perf_counter()-begin;r['tokenize_seconds']=tokenize;return r
 for q in qs:
  a=run(q['prompt'],budget=16);references[q['id']]=a['ids']
  for size in children:
   b=run(q['prompt'],size,budget=16);parity.append({'id':q['id'],'size':size,'reference_ids':a['ids'],'speculative_ids':b['ids'],'identical':a['ids']==b['ids'],'proposed':b['proposed'],'accepted':b['accepted']});save_json(H/'reports/parity.json',{'rows':parity,'complete':False})
 for size in children:modes[size]='block' if all(x['identical'] for x in parity if x['size']==size) else 'serial'
 save_json(H/'reports/parity.json',{'rows':parity,'complete':True,'selected_correctness_modes':modes,'finite_domain_not_universal_proof':True})
 # Fixed warmup per variant. These timings are retained but not counted in pairs.
 warm=[{'variant':'target',**run(qs[0]['prompt'])}]
 for size in children:warm.append({'variant':size,**run(qs[0]['prompt'],size,mode=modes[size])})
 save_json(H/'reports/timing_warmups.json',warm);rows=[];byid={q['id']:q for q in qs}
 for size in ['small','large']:
  for pair in range(6):
   q=byid[cfg['timing_prompt_ids'][pair//2]];order=['target',size] if pair%2==0 else [size,'target'];results={}
   for v in order:results[v]=run(q['prompt'],None if v=='target' else size,mode=modes[size])
   a,b=results['target'],results[size];rows.append({'size':size,'pair':pair,'id':q['id'],'order':order,'mode':modes[size],'target':a,'speculative':b,'identical':a['ids']==b['ids'],'resident_speed_ratio':a['resident_request_seconds']/b['resident_request_seconds'],'all_overhead_included':True});save_json(report,rows);print('TIMING026',size,pair,rows[-1]['identical'],rows[-1]['resident_speed_ratio'],flush=True)
 summary={'status':'complete','hardware':'cloud x86 CPU quota2,4threads; not Android','model_load_seconds_excluded_from_resident_requests':loads,'model_target_parent_sha256':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8','all_pairs_included':True,'models':{}}
 for size in children:
  rr=[r for r in rows if r['size']==size];a=sum(r['target']['resident_request_seconds'] for r in rr);b=sum(r['speculative']['resident_request_seconds'] for r in rr);proposed=sum(r['speculative']['proposed'] for r in rr);accepted=sum(r['speculative']['accepted'] for r in rr);diffs=[r['target']['resident_request_seconds']-r['speculative']['resident_request_seconds'] for r in rr];observed=abs(sum(diffs));extreme=sum(abs(sum(d*(1 if mask>>i&1 else -1) for i,d in enumerate(diffs)))>=observed-1e-12 for mask in range(1<<len(diffs)));p=extreme/(1<<len(diffs));exact=all(r['identical'] for r in rr);summary['models'][size]={'target_total_seconds':a,'speculative_total_seconds':b,'speed_ratio_total':a/b,'mean_pair_ratio':statistics.mean(r['resident_speed_ratio'] for r in rr),'all_target_token_streams_identical':exact,'acceptance':accepted/proposed if proposed else 0.,'proposed':proposed,'accepted':accepted,'verification_mode':modes[size],'fixed_pairs':6,'paired_sign_flip_p_two_sided':p,'measured_cpu_benefit_with_matching_tokens':exact and a>b and p<.05,'no_universal_lossless_or_phone_claim':True}
 save_json(H/'reports/speed_summary.json',summary);print('BENCHMARK026_COMPLETE',summary['models'],flush=True)
if __name__=='__main__':main()
