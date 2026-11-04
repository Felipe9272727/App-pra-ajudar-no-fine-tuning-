"""Finite local continuation; no duplicate completed rounds or hidden restarts."""
import json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rsi100.watchdog import supervise
HERE=ROOT/'local_cpu'

def run(*args):
    print('LOCAL_STAGE',args,flush=True)
    code=supervise([sys.executable,'-u',str(HERE/'runner.py'),*map(str,args)],ROOT/'rsi100/live_progress.json',max_seconds=4500)
    if code:raise RuntimeError(f'Local stage {args} failed with {code}; saved checkpoint remains authoritative')

def main():
    assert os.environ['LS_CPU_THREADS']=='4'
    for start in range(1,101,10):
        status=json.loads((ROOT/'rsi100/status.json').read_text())
        if status['rounds_completed']<start+9:
            run('chunk','--start',start,'--stop',start+9)
    if not (ROOT/'rsi100/frozen.json').exists():run('freeze')
    frozen=json.loads((ROOT/'rsi100/frozen.json').read_text())
    for variant in frozen['final_variants']:
        for shard in (0,1):
            p=ROOT/'rsi100'/f'final_{variant}_{shard}.json'
            if not p.exists():run('final','--variant',variant,'--shard',shard)
    run('report')
    print('LOCAL_SEARCH_COMPLETE',flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        (HERE/'controller_failure.json').write_text(json.dumps({'error':str(exc),'unix':time.time()})+'\n')
        raise
