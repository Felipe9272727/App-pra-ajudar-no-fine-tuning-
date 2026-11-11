"""Resume only missing phases; verify existing checkpoints, never overwrite them.

First inspect status/logs and ensure the old worker is dead. Completed study is
a no-op. Initial run_study.py is an archival initial-run script, not a resumer.
"""
import hashlib,json,os
from pathlib import Path
import run_study as study
HERE=Path(__file__).resolve().parent

def main():
    me=os.getpid()
    for p in Path('/proc').iterdir():
        if not p.name.isdigit() or int(p.name)==me:continue
        try:args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
        except OSError:continue
        names=['run_study.py','teach.py','evaluate.py','check_mechanism.py','resume_study.py']
        if args and Path(args[0]).name.startswith('python') and any(a in ['review013/'+name,str(HERE/name)] for a in args[1:] for name in names):
            raise RuntimeError('Existing study worker detected: inspect logs/processes first, pid='+p.name)
    fit=json.loads((HERE/'fit.json').read_text())
    for kind,meta in fit['candidates'].items():
        assert hashlib.sha256((HERE/'checkpoints'/(kind+'.pt')).read_bytes()).hexdigest()==meta['sha256']
    if (HERE/'selection.json').exists():
        old=json.loads((HERE/'selection.json').read_text())
        if old['status']=='complete_both_rejected_screen':
            print('STUDY ALREADY COMPLETE; CHECKPOINT HASHES VERIFIED; ZERO PHASES REPEATED');return
    original=study.command
    def guarded(script,*args):
        if script=='teach.py' and args==('fit',):return
        if script=='check_mechanism.py' and (HERE/'mechanism.json').exists():
            assert json.loads((HERE/'mechanism.json').read_text())['status']=='complete';return
        if script=='evaluate.py':
            kind,phase=args;path=HERE/(phase+'_'+kind+'.json')
            if path.exists() and json.loads(path.read_text()).get('status')=='complete':return
        original(script,*args)
    try:
        guarded('check_mechanism.py')
        for kind in ['original','parent','loop','joint']:
            guarded('evaluate.py',kind,'screen');guarded('evaluate.py',kind,'controls')
            if kind in ['loop','joint']:guarded('evaluate.py',kind,'learning_diagnostic')
        from finalize import main as finalize
        finalize()
    finally:
        p=HERE/'status.json';s=json.loads(p.read_text());s['model_process_active']=False;s['process_continues_in_background']=False;p.write_text(json.dumps(s,indent=2)+'\n')

if __name__=='__main__':main()
