"""Resume only missing declared diagnostics, serially, with durable progress."""
import os,sys,json,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reasoning018'
def status(phase,active):
 data={'status':phase,'model_process_active':active,'checkpoint_promoted':False,'optimizer_steps_completed':8,'process_continues_in_background':False};p=HERE/'status.json';tmp=p.with_suffix('.json.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(p)
def run(args,log):
 with log.open('x') as f:subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
def main():
 assert hashlib.sha256((HERE/'checkpoints/candidate.pt.gz').read_bytes()).hexdigest()=='f25aac86011be54f5025f24be391a1f7076a7d4e9de234e05f4ead20ecf729ab'
 for v in ['candidate','parent','original']:
  p=HERE/f'long1024_{v}.json'
  if p.exists():
   d=json.loads(p.read_text());assert d['effective_budget']==1024 and not d['selection_allowed'];continue
  status('diagnosing_long1024_'+v,True);run([sys.executable,str(HERE/'long_budget.py'),v],HERE/f'long_{v}_resumed.log')
 status('confirmatory_host_timing',True)
 bench=Path('/dev/shm/liquid-android/prebuilt/speed017/bench');meta=json.loads((ROOT/'speed017/reports/host_binary.json').read_text());assert hashlib.sha256(bench.read_bytes()).hexdigest()==meta['sha256']
 for trial in [1,2,3]:
  p=ROOT/f'speed017/reports/confirm_timing_{trial}.json'
  if p.exists():assert len(json.loads(p.read_text())['rows'])==10;continue
  with p.open('x') as f, (ROOT/f'speed017/reports/confirm_timing_{trial}.log').open('x') as log:
   subprocess.run([str(bench),'speed017/model_locator.json','time','speed017/timing_ids_extended.json'],cwd=ROOT,stdout=f,stderr=log,check=True)
 status('all_registered_diagnostics_complete_pending_report',False)
if __name__=='__main__':
 try:main()
 except Exception:
  status('diagnostic_execution_error_inspect_before_resuming',False);raise
