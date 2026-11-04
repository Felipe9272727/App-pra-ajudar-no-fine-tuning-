"""Durable generated checkpoints, without overwriting concurrent source edits."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BRANCH='codex/liquid-sense-rsi-cycle2-20261104'

def allowed(path):
    if path in ['LAB_REPORT.md','checkpoints/liquid_sense_loop.json']:return True
    return bool(re.fullmatch(r'lab_rsi/(?:status|archive|frozen|summary|fit_metadata|validation_queue|screening_cache_check|development_[a-zA-Z0-9_]+|validation_[a-zA-Z0-9_]+|heldout_[a-zA-Z0-9_]+|round_\d+|progress|ci_[a-zA-Z0-9_-]+_runtime)\.json',path) or re.fullmatch(r'lab_rsi/candidate_0[123]\.pt',path))

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def guard():
    source=os.environ['GITHUB_SHA']
    git('merge-base','--is-ancestor',source,'HEAD')
    changed=git('diff','--name-only',source,'HEAD').splitlines()
    bad=[p for p in changed if not allowed(p)]
    if bad:raise RuntimeError('Source changed during run: '+repr(bad))
    progress=ROOT/'lab_rsi/progress.json'
    if progress.exists():
        info=json.loads(progress.read_text())
        if info['run_id']!=os.environ['GITHUB_RUN_ID']:
            raise RuntimeError('Concurrent checkpoint from another Actions run')

def publish(phase):
    if os.environ.get('GITHUB_ACTIONS')!='true':return
    guard()
    state=ROOT/'lab_rsi/progress.json'
    state.write_text(json.dumps({'run_id':os.environ['GITHUB_RUN_ID'],'source_commit':os.environ['GITHUB_SHA'],'phase':phase},indent=2)+'\n')
    paths=set(git('diff','--name-only','HEAD').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    paths=sorted(p for p in paths if allowed(p))
    if not paths:return
    git('config','user.name','github-actions[bot]')
    git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('add','--',*paths)
    git('commit','-m',f'Save RSI cycle 2: {phase}')
    # Reject a concurrent head change; no force/rebase or source overwrite.
    git('push','origin',f'HEAD:refs/heads/{BRANCH}')
    print('CHECKPOINT_SAVED',phase,git('rev-parse','HEAD'),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase');a=p.parse_args()
    if a.phase=='guard':guard()
    else:publish(a.phase)
