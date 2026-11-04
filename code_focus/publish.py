"""Persist localized weight patches and decisions without touching other runs."""
import json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BRANCH='codex/liquid-sense-code-focus-20261104'
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
def allowed(p):return bool(p=='CODE_FOCUS_REPORT.md' or re.fullmatch(r'code_focus/(?:status|progress|parent_import|localization|archive|validation_queue|frozen|summary|development_[a-z0-9_]+|validation_[a-z0-9_]+|final_[a-z0-9_]+)\.json',p) or re.fullmatch(r'code_focus/checkpoints/[a-z0-9_]+\.pt',p))
def guard():
 git('merge-base','--is-ancestor',os.environ['GITHUB_SHA'],'HEAD')
 if any(not allowed(p) for p in git('diff','--name-only',os.environ['GITHUB_SHA'],'HEAD').splitlines()):raise RuntimeError('Concurrent source change')
 p=ROOT/'code_focus/progress.json'
 if p.exists() and json.loads(p.read_text())['run_id']!=os.environ['GITHUB_RUN_ID']:raise RuntimeError('Another run owns progress')
def publish(phase):
 if os.environ.get('GITHUB_ACTIONS')!='true':return
 guard();(ROOT/'code_focus/progress.json').write_text(json.dumps({'run_id':os.environ['GITHUB_RUN_ID'],'source_commit':os.environ['GITHUB_SHA'],'phase':phase},indent=2)+'\n')
 paths=set(git('diff','--name-only','HEAD').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines());paths=sorted(p for p in paths if allowed(p))
 if not paths:return
 git('config','user.name','github-actions[bot]');git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
 git('add','--',*paths);git('commit','-m','Code focus: '+phase);git('push','origin','HEAD:refs/heads/'+BRANCH)
 print('SAVED',phase,git('rev-parse','HEAD'),flush=True)
if __name__=='__main__':
 import sys
 guard() if sys.argv[1]=='guard' else publish(sys.argv[1])
