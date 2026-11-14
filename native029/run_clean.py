"""One offline, credential-free model worker; exact process lifecycle journal."""
import json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
phase=sys.argv[1];assert phase in ['prepare','train','evaluate','policy','diagnose_loop','select','tools_evaluate','final_evaluate']
def save(p,v):
    q=p.with_suffix('.tmp');q.write_text(json.dumps(v,indent=2)+'\n');q.replace(p)
runtime=H/'runtime.json'
if runtime.exists():
    old=json.loads(runtime.read_text());pid=old.get('pid')
    if pid and Path(f'/proc/{pid}').exists():raise RuntimeError('Inspect existing worker before restarting')
s=json.loads((H/'status.json').read_text());s.update(status='running_'+phase,model_process_active=True,phase=phase);save(H/'status.json',s)
env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','LS_CPU_THREADS':'4','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'}
p=subprocess.Popen([sys.executable,'-u',str(H/(phase+'.py')),*sys.argv[2:]],cwd=ROOT,env=env)
save(runtime,{'phase':phase,'pid':p.pid,'model_process_active':True,'single_worker':True,'credentials_forwarded':False})
result=p.wait();s=json.loads((H/'status.json').read_text());s.update(status='completed_'+phase if result==0 else 'failed_'+phase,model_process_active=False,last_exit_code=result);save(H/'status.json',s)
save(runtime,{'phase':phase,'pid':None,'model_process_active':False,'last_exit_code':result});raise SystemExit(result)
