"""Separate bounded post-selection arithmetic diagnostic, no credentials."""
import json,os,sys,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
stage=sys.argv[1];assert stage in ['sft_final','policy_final']
def read(p):return json.loads((H/p).read_text())
def save(p,v):
    dest=H/p;tmp=dest.with_suffix('.tmp');tmp.write_text(json.dumps(v,indent=2)+'\n');tmp.replace(dest)
assert read('status.json')['status']=='complete' and not read('runtime.json')['model_process_active']
assert (H/'selection.json').exists()
pth=H/'arithmetic_runtime.json'
if pth.exists():
    old=read('arithmetic_runtime.json');assert not old.get('pid') or not Path('/proc/'+str(old['pid'])).exists()
if (H/f'reports/arithmetic_{stage}.json').exists():
    assert read(f'reports/arithmetic_{stage}.json').get('status')!='complete','Completed diagnostic must not repeat'
s=read('status.json');s.update(status='running_arithmetic_audit',model_process_active=True);save('status.json',s)
env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','LS_CPU_THREADS':'4','HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'}
p=subprocess.Popen([sys.executable,'-u',str(H/'diagnose_merge.py'),stage],cwd=ROOT,env=env)
save('arithmetic_runtime.json',{'pid':p.pid,'stage':stage,'model_process_active':True,'credentials_forwarded':False})
code=p.wait();s=read('status.json');s.update(status='complete' if code==0 else 'failed_arithmetic_audit',model_process_active=False,last_arithmetic_exit_code=code);save('status.json',s)
save('arithmetic_runtime.json',{'pid':None,'stage':stage,'model_process_active':False,'exit_code':code});raise SystemExit(code)
