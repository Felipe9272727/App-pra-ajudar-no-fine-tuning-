"""Sequential preregistered phases after the active SFT worker exits."""
import json,os,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent

def read(p):return json.loads((H/p).read_text())
def run(phase,*args):
    label=phase+('_'+'_'.join(args).replace('--','') if args else '')
    log=H/'logs'/(label+'.log')
    assert not log.exists(),'Inspect existing phase log before a possible resume: '+str(log)
    print('PHASE028_START',phase,*args,flush=True)
    with log.open('w') as f:
        result=subprocess.run([sys.executable,'-u',str(H/'run_clean.py'),phase,*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
    assert result.returncode==0,'Stopped; inspect '+str(log)
    print('PHASE028_END',phase,*args,flush=True)

def main():
    assert not (H/'summary.json').exists(),'Completed study must not be repeated'
    state=read('runtime.json');pid=state.get('pid')
    if pid:
        assert state['phase']=='train','Unexpected active phase'
        while Path(f'/proc/{pid}').exists():time.sleep(1)
        # The credential-free parent writes the lifecycle journal on worker exit.
        for _ in range(10):
            if not read('runtime.json').get('model_process_active'):break
            time.sleep(.2)
    assert read('status.json').get('last_exit_code')==0,'Inspect failed prior phase'
    assert (H/'checkpoints/sft_final/manifest.json').exists()
    assert read('reports/sft_training.json')['steps']==96
    run('policy')
    for variant in ['original','parent','sft_final','policy_final']:run('evaluate',variant)
    run('evaluate','--select');selection=read('selection.json');winner=selection['selected']
    if winner:
        for variant in ['original','parent',winner]:run('final_evaluate',variant)
    for variant in ['parent',winner or 'policy_final']:run('diagnose_loop',variant)
    for variant in ['original','parent','sft_final','policy_final']:run('tools_evaluate',variant)
    assert not read('runtime.json').get('model_process_active')
    # Summary has no model generation; all mutable comparisons are complete.
    result=subprocess.run([sys.executable,'-u',str(H/'report.py')],cwd=ROOT)
    assert result.returncode==0
    print('FIXED028_COMPLETE_ALL_WORKERS_CLOSED',flush=True)
if __name__=='__main__':main()
