"""Finite sequential evaluation after the four-epoch worker closes."""
import json,sys,subprocess,time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent

def read(p):return json.loads((H/p).read_text())
def run(*args):
    label='_'.join(args).replace('--','');log=H/'logs'/(label+'.log');assert not log.exists(),'Inspect existing phase before resume'
    print('PHASE029_START',*args,flush=True)
    with log.open('w') as f:r=subprocess.run([sys.executable,'-u',str(H/'run_clean.py'),*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    assert r.returncode==0,'Inspect '+str(log);print('PHASE029_END',*args,flush=True)

def main():
    assert not (H/'summary.json').exists()
    state=read('runtime.json');pid=state.get('pid')
    if pid:
        assert state['phase']=='train'
        while Path(f'/proc/{pid}').exists():time.sleep(1)
        for j in range(10):
            if not read('runtime.json').get('model_process_active'):break
            time.sleep(.2)
    assert read('status.json')['last_exit_code']==0
    assert (H/'checkpoints/epoch04/manifest.json').exists() and read('reports/sft_training.json')['steps']==192
    names=['original','parent']+[f'epoch{i:02d}' for i in range(1,5)]
    for v in names:
        run('evaluate',v)
        if v!='original':run('evaluate',v,'--split','legacy')
    run('evaluate','--select');s=read('selection.json')
    if s['selected']:
        for v in ['original','parent',s['selected']]:run('evaluate',v,'--split','final')
    assert not read('runtime.json')['model_process_active']
    r=subprocess.run([sys.executable,'-u',str(H/'report.py')],cwd=ROOT);assert r.returncode==0
    print('FOUR_EPOCH029_ALL_WORKERS_CLOSED',flush=True)
if __name__=='__main__':main()
