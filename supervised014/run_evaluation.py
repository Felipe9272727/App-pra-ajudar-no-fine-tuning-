"""Serial, bounded, resumable; all second-benchmark evaluations always run."""
import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def main():
    assert (HERE/'teaching.json').exists(),'Finish and preserve candidate before evaluation'
    for role in ['taught','transfer','controls']:
        for kind in ['original','parent','edited']:
            path=HERE/(role+'_'+kind+'.json')
            if path.exists() and json.loads(path.read_text()).get('status')=='complete':continue
            s=json.loads((HERE/'status.json').read_text());s.update(status='evaluating_'+role+'_'+kind,model_process_active=True,updated_unix=time.time());(HERE/'status.json').write_text(json.dumps(s,indent=2)+'\n')
            subprocess.run([sys.executable,str(HERE/'evaluate.py'),kind,role],cwd=ROOT,check=True)
    s=json.loads((HERE/'status.json').read_text());s.update(status='all_model_evaluations_complete_pending_report',model_process_active=False,updated_unix=time.time());(HERE/'status.json').write_text(json.dumps(s,indent=2)+'\n')
if __name__=='__main__':
    try:main()
    finally:
        p=HERE/'status.json';s=json.loads(p.read_text());s['model_process_active']=False;s['process_continues_in_background']=False;p.write_text(json.dumps(s,indent=2)+'\n')
