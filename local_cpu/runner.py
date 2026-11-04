"""Use the existing forward-only search on local CPU with an isolated judge."""
import argparse,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'rsi100'))
import engine as e
from local_cpu import publisher,sandbox
e.pub=publisher;e.cr.evaluate=sandbox.evaluate
original_provenance=e.provenance
def provenance():
    data=original_provenance();data['source_commit']=os.environ['LS_SOURCE_COMMIT']
    data['execution']='local managed CPU';data['session']=os.environ['LS_LOCAL_SESSION']
    data['protocol']['executor']='capability-cleared syscall-filtered subprocess; same AST judge'
    for name in ['runner.py','sandbox.py','publisher.py','controller.py']:
        p=ROOT/'local_cpu'/name;data['code_sha256'][str(p.relative_to(ROOT))]=e.cr.file_hash(p)
    return data
e.provenance=provenance

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['chunk','freeze','final','report'])
    p.add_argument('--start',type=int);p.add_argument('--stop',type=int);p.add_argument('--variant');p.add_argument('--shard',type=int);a=p.parse_args()
    try:
        if a.phase=='chunk':e.chunk(a.start,a.stop)
        elif a.phase=='freeze':e.freeze()
        elif a.phase=='final':
            e.final(a.variant,a.shard);publisher.publish(f'final {a.variant} shard {a.shard}')
        else:e.report();publisher.publish('complete local search and final report')
    except Exception:
        e.state(status='interrupted',model_process_active=False)
        e.export('local-failure')
        raise
