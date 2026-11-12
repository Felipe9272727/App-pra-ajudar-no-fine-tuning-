"""Summarize raw paired timing and exact equivalence without phone extrapolation."""
import json,statistics,itertools,math,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
read=lambda n:json.loads((HERE/'reports'/n).read_text())
time=read('timing_extended.json');rows=[r for r in time['rows'] if not r['warmup']]
pairs=[]
for i in range(0,len(rows),2):
 a=next(r for r in rows[i:i+2] if not r['optimized']);b=next(r for r in rows[i:i+2] if r['optimized']);pairs.append({'reference_run':a['run'],'optimized_run':b['run'],'reference_seconds':a['seconds'],'optimized_seconds':b['seconds'],'seconds_saved':a['seconds']-b['seconds'],'ratio':a['seconds']/b['seconds']})
diffs=[p['seconds_saved'] for p in pairs];observed=statistics.mean(diffs)
permuted=[abs(statistics.mean(s*d for s,d in zip(signs,diffs))) for signs in itertools.product([-1,1],repeat=len(diffs))]
p=sum(v>=abs(observed)-1e-12 for v in permuted)/len(permuted)
a=[r['seconds'] for r in rows if not r['optimized']];b=[r['seconds'] for r in rows if r['optimized']]
cihalf=3.182446305*statistics.stdev(diffs)/math.sqrt(len(diffs))
x=read('chat_reference.json');y=read('chat_fast.json');conversations=[]
for i,(base,opt) in enumerate(zip(x,y)):
 assert base['generated_ids']==opt['generated_ids'] and base['text']==opt['text'] and base['finish_reason']==opt['finish_reason']
 conversations.append({'case':i,'generated_token_ids_identical':True,'tokens':base['tokens'],'reused_prompt_tokens':opt['reused_prompt_tokens'],'reference_prefill_seconds':base['prefill_seconds'],'optimized_prefill_seconds':opt['prefill_seconds'],'prefill_ratio':base['prefill_seconds']/opt['prefill_seconds'],'reference_decode_seconds':base['decode_seconds'],'optimized_decode_seconds':opt['decode_seconds']})
trace=read('exact_trace_extended.json');assert len(trace['steps'])==16 and all(all(s[k] for k in ['all_57_hidden_states_bits_equal','all_56_cache_slots_bits_equal','all_248320_logits_bits_equal']) for s in trace['steps'])
source=json.loads((HERE/'baseline_source_hashes.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in source.items())
out={'status':'completed_host_prototype','weights_changed':False,'baseline_android_source_unchanged':True,'physical_layers':32,'executions_per_token':56,'threads':4,'unit_tests_passed':7,'trace_steps_bit_identical':16,'hidden_states_compared':16*57,'cache_slots_compared':16*56,'logits_compared':16*248320,'chat_cases_token_identical':3,'chat_generated_tokens_compared':sum(r['tokens'] for r in x),'timing_scope':'x86 CPU backbone, excludes vocabulary projection and tokenizer; not Android phone','timing_pairs':pairs,'mean_reference_seconds_per16':statistics.mean(a),'mean_optimized_seconds_per16':statistics.mean(b),'mean_ratio':statistics.mean(a)/statistics.mean(b),'mean_time_reduction_fraction':1-statistics.mean(b)/statistics.mean(a),'paired_mean_seconds_saved':observed,'paired_difference_t_95_ci':[observed-cihalf,observed+cihalf],'paired_sign_flip_two_sided_p':p,'timing_statistically_confirmed_at_0_05':p<.05,'chat_observations':conversations,'limitations':['Four timing pairs only; CPU timing differences are noisy and interval includes zero.','Repeated layers have exact preserved computations; this is not an intelligence improvement.','Conversation latency comparisons are single observations, not randomized confidence intervals.','Finite exactness checks are not a proof for every possible prefix or ARM floating-point backend.','Prototype source and host executable only; installed0.1.0 APK remains unchanged.']}
(HERE/'reports/summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['trace_steps_bit_identical','chat_generated_tokens_compared','mean_ratio','mean_time_reduction_fraction','paired_sign_flip_two_sided_p']}))
