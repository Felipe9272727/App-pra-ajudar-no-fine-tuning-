"""Fixed paired timing for017confirmation or019new optimization."""
import argparse,json,statistics,itertools,math,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('study',choices=['speed017','speed019']);a=p.parse_args();root=Path(__file__).resolve().parents[1];here=root/a.study;prefix='confirm_timing_' if a.study=='speed017' else 'timing_';pairs=[];runs=[]
for i in [1,2,3]:
 d=json.loads((here/'reports'/f'{prefix}{i}.json').read_text());assert len(d['rows'])==10 and d['threads']==4;rows=[r for r in d['rows'] if not r['warmup']];assert len(rows)==8;runs+=rows
 for j in range(0,8,2):
  x=next(r for r in rows[j:j+2] if not r['optimized']);y=next(r for r in rows[j:j+2] if r['optimized']);pairs.append({'process':i,'reference_run':x['run'],'optimized_run':y['run'],'reference_seconds':x['seconds'],'optimized_seconds':y['seconds'],'saved_seconds':x['seconds']-y['seconds'],'ratio':x['seconds']/y['seconds']})
dif=[r['saved_seconds'] for r in pairs];mean=statistics.mean(dif);perms=[abs(statistics.mean(s*d for s,d in zip(signs,dif))) for signs in itertools.product([-1,1],repeat=12)];pv=sum(v>=abs(mean)-1e-12 for v in perms)/len(perms);half=2.200985160*statistics.stdev(dif)/math.sqrt(12);ref=statistics.mean(r['reference_seconds'] for r in pairs);opt=statistics.mean(r['optimized_seconds'] for r in pairs)
result={'study':a.study,'fixed_pairs':12,'warmup_rows_excluded':6,'timed_rows':24,'timing_scope':'cloudx86fourthreads16tokenbackbone; vocabulary readout excluded; not a phone measurement','reference_mean_seconds':ref,'optimized_mean_seconds':opt,'mean_ratio':ref/opt,'time_reduction_fraction':1-opt/ref,'paired_mean_seconds_saved':mean,'paired_95_ci':[mean-half,mean+half],'exact_sign_flip_two_sided_p':pv,'confirmed_cloud_cpu_benefit':pv<.05 and mean-half>0,'pairs':pairs,'all_preregistered_pairs_included':True,'no_further_timing_repetition':True,'weights_changed':False,'quality_promotion':False}
if a.study=='speed019':
 trace=json.loads((here/'reports/exact_trace.json').read_text());assert len(trace['steps'])==16 and trace['proven_zero_matrices']==16 and trace['zero_mv_shortcut_hits']==512
 assert all(all(s[k] for k in ['all_57_hidden_states_bits_equal','all_56_cache_slots_bits_equal','all_248320_logits_bits_equal']) for s in trace['steps'])
 x=json.loads((here/'reports/chat_reference.json').read_text());y=json.loads((here/'reports/chat_fast.json').read_text());assert all(a['generated_ids']==b['generated_ids'] and a['text']==b['text'] and a['finish_reason']==b['finish_reason'] for a,b in zip(x,y)) and len(x)==len(y)==3
 result.update(all16_trace_steps_bit_identical=True,zero_matrices_verified=16,zero_mv_hits=512,all56_cache_slots_preserved=True,chat_cases_identical=3,generated_chat_tokens_identical=sum(r['tokens'] for r in x),android_apk_updated=False)
 out=here/'reports/summary.json'
else:out=here/'reports/confirmation_summary.json'
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['study','mean_ratio','paired_95_ci','exact_sign_flip_two_sided_p','confirmed_cloud_cpu_benefit']}))
