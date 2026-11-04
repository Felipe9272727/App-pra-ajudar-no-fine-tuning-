"""Every completed decision is a non-forced durable Git commit."""
import json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BRANCH='codex/liquid-sense-rsi100-20261104'
def git(*a):
 return subprocess.check_output(['git',*a],cwd=ROOT,text=True,timeout=60,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'}).strip()
def allowed(p):return bool(p=='RSI100_REPORT.md' or re.fullmatch(r'rsi100/(?:status|progress|calibration_\d{3}|best_metrics|baseline_metrics|frozen|summary|validation_[a-z0-9_]+|final_[a-z0-9_]+|round_\d{3})\.json',p) or re.fullmatch(r'rsi100/checkpoints/(?:baseline|best|accepted_\d{3})\.pt',p))
def guard():
 git('merge-base','--is-ancestor',os.environ['GITHUB_SHA'],'HEAD')
 if any(not allowed(p) for p in git('diff','--name-only',os.environ['GITHUB_SHA'],'HEAD').splitlines()):raise RuntimeError('Concurrent source edit')
 p=ROOT/'rsi100/progress.json'
 if p.exists() and json.loads(p.read_text())['run_id']!=os.environ['GITHUB_RUN_ID']:raise RuntimeError('Different run owns checkpoints')
def publish(phase):
 if os.environ.get('GITHUB_ACTIONS')!='true':return
 guard()
 (ROOT/'rsi100/progress.json').write_text(json.dumps({'run_id':os.environ['GITHUB_RUN_ID'],'source_commit':os.environ['GITHUB_SHA'],'phase':phase},indent=2)+'\n')
 paths=set(git('diff','--name-only','HEAD').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
 paths=sorted(p for p in paths if allowed(p))
 if not paths:return
 git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
 git('add','--',*paths);git('commit','-m','RSI100: '+phase)
 local=git('rev-parse','HEAD')
 try:git('push','origin','HEAD:refs/heads/'+BRANCH)
 except (subprocess.TimeoutExpired,subprocess.CalledProcessError):
  # An interrupted response can conceal a successful push. Verify before
  # declaring failure; never repeat an uncertain mutation or force a ref.
  remote=git('ls-remote','origin','refs/heads/'+BRANCH).split()[0]
  if remote!=local:raise
 print('SAVED',phase,git('rev-parse','HEAD'),flush=True)
if __name__=='__main__':
 import sys
 guard() if sys.argv[1]=='guard' else publish(sys.argv[1])
