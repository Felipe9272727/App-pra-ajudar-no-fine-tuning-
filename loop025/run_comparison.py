"""Serial CLI orchestration only; frozen evaluation and gates stay unchanged."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'loop025';env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LS_CPU_THREADS':'4','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'}
def run(args,label):
 status={'status':'comparing','phase':label,'optimizer_steps':24,'epochs':3,'model_process_active':True,'checkpoint_promoted':False,'independent_test_queried':(H/'selection.json').exists() and json.loads((H/'selection.json').read_text()).get('selected_epoch') is not None};(H/'status.json').write_text(json.dumps(status,indent=2)+'\n')
 with (H/'logs'/f'{label}.log').open('a') as log:
  p=subprocess.Popen([sys.executable,'-u',*args],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT);(H/'runtime.json').write_text(json.dumps({'pid':p.pid,'phase':label,'single_model_worker':True,'credentials_forwarded':False},indent=2)+'\n');result=p.wait()
 status['model_process_active']=False;status['last_exit_code']=result;(H/'status.json').write_text(json.dumps(status,indent=2)+'\n');assert result==0,(label,result);print('PHASE025_FINISHED',label,flush=True)
assert (H/'cold_restore.json').exists()
for variant in ['original','parent','epoch1','epoch2','epoch3']:run(['loop025/evaluate.py',variant],'development_'+variant)
run(['loop025/choose_epoch.py'],'select_epoch');selection=json.loads((H/'selection.json').read_text());chosen=selection['selected_epoch']
if chosen is not None:
 for variant in ['original','parent','epoch'+str(chosen)]:run(['loop025/evaluate.py',variant,'--phase','final'],'final_'+variant)
for variant in ['parent','epoch'+str(chosen or 3)]:run(['loop025/evaluate.py',variant,'--bypass'],'bypass_'+variant)
(H/'status.json').write_text(json.dumps({'status':'comparison_complete_pending_report','optimizer_steps':24,'epochs':3,'model_process_active':False,'checkpoint_promoted':False,'selected_epoch':chosen,'independent_test_queried':chosen is not None,'active_runs':[]},indent=2)+'\n');print('ALL025_COMPARISONS_COMPLETE',flush=True)
