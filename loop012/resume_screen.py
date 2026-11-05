"""Recover only missing scoring rows after an executor interruption."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from loop012.core import *
@torch.inference_mode()
def main():
 p=argparse.ArgumentParser();p.add_argument('kind',choices=['parent','target','inverse']);a=p.parse_args();verify()
 path=HERE/f'screen_{a.kind}.json'
 if path.exists():
  report=json.loads(path.read_text())
  if report['status']=='complete':print('Already complete; no generation repeated.');return
  assert report['variant']==a.kind and {r['id'] for r in report['rows']}<=set(SCREEN)
 else:report={'status':'running','rows':[],'controls':[],'variant':a.kind}
 m,t,meta=load_variant(a.kind)
 if a.kind!='parent' and 'model' in report:assert report['model']['gate_patch_sha256']==meta['gate_patch_sha256']
 report['model']=meta;state('resumed_screen_'+a.kind,True)
 for row in tasks(SCREEN):
  if row['id'] not in {r['id'] for r in report['rows']}:report['rows']+=e.coding(m,t,[row]);save(path.name,report)
 report.update(status='complete',tasks_passed=sum(r['all_passed'] for r in report['rows']),cases_passed=sum(r['passed'] for r in report['rows']));save(path.name,report);state(path.stem+'_complete')
if __name__=='__main__':main()
