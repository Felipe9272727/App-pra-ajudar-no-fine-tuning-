"""Save only generated coding-experiment artifacts, never overwrite source."""
import json
import os
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
BRANCH='codex/liquid-sense-code-rsi-20261104'

def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def allowed(path):
    return bool(path=='CODE_REPORT.md' or re.fullmatch(r'code_rsi/(?!data\.json$|run_request\.json$|manifest\.json$)[a-zA-Z0-9_-]+\.json',path) or re.fullmatch(r'code_rsi/checkpoints/[a-zA-Z0-9_-]+\.pt',path))
def guard():
    git('merge-base','--is-ancestor',os.environ['GITHUB_SHA'],'HEAD')
    changes=git('diff','--name-only',os.environ['GITHUB_SHA'],'HEAD').splitlines()
    if any(not allowed(p) for p in changes):raise RuntimeError('Concurrent source edit; keep artifacts and stop')
    p=ROOT/'code_rsi/progress.json'
    if p.exists() and json.loads(p.read_text())['run_id']!=os.environ['GITHUB_RUN_ID']:
        raise RuntimeError('Another run advanced these checkpoints')
def publish(phase):
    if os.environ.get('GITHUB_ACTIONS')!='true':return
    guard()
    (ROOT/'code_rsi/progress.json').write_text(json.dumps({'run_id':os.environ['GITHUB_RUN_ID'],'source_commit':os.environ['GITHUB_SHA'],'phase':phase},indent=2)+'\n')
    paths=set(git('diff','--name-only','HEAD').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    paths=sorted(p for p in paths if allowed(p))
    if not paths:return
    git('config','user.name','github-actions[bot]')
    git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('add','--',*paths);git('commit','-m','Coding RSI: '+phase)
    git('push','origin','HEAD:refs/heads/'+BRANCH)
    print('SAVED',phase,git('rev-parse','HEAD'),flush=True)
if __name__=='__main__':
    import sys
    if sys.argv[1]=='guard':guard()
    else:publish(sys.argv[1])
