"""Run the paired *observed development* 4B baseline on a suitable CPU machine.

No download, fine-tuning or cloud dispatch. Requires the exact pinned snapshot
already on disk. Fresh confirmatory LiveCodeBench needs its own frozen manifest.
"""
import argparse,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'diagnostic011'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import e,torch
from diagnostic011.run import PROTOCOL
from diagnostic011.metric import compare
from transformers import AutoTokenizer,Qwen3_5ForConditionalGeneration

@torch.inference_mode()
def main():
 p=argparse.ArgumentParser();p.add_argument('--model-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 reference=json.loads((HERE/'reference_4b.json').read_text());spec=json.loads((HERE/'reference_4b_files.json').read_text())
 assert spec['revision']==reference['revision'];assert spec['files']
 for name,digest in spec['files'].items():
  with (a.model_dir/name).open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
  assert actual==digest,name
 torch.set_num_threads(4);torch.set_grad_enabled(False)
 model=Qwen3_5ForConditionalGeneration.from_pretrained(a.model_dir,local_files_only=True,dtype=torch.bfloat16,attn_implementation='eager').eval().requires_grad_(False)
 tok=AutoTokenizer.from_pretrained(a.model_dir,local_files_only=True);small_tok=e.cr.tokenizer()
 report=json.loads(a.output.read_text()) if a.output.exists() else {'status':'running','model_id':reference['model_id'],
  'model_revision':reference['revision'],'protocol':PROTOCOL,'loaded_parameters':sum(p.numel() for p in model.parameters()),
  'scope':'observed internal development; no independent superiority claim','rows':[]}
 assert report['model_revision']==reference['revision'] and report['protocol']==PROTOCOL
 for task in e.DATA['search']+e.DATA['guard']:
  if task['id'] in {r['id'] for r in report['rows']}:continue
  assert torch.equal(e.cr.prompt(tok,task['prompt']),e.cr.prompt(small_tok,task['prompt'])),'Actual context/tokenization differs'
  report['rows']+=e.coding(model,tok,[task]);e.cr.atomic_json(a.output,report)
 report['status']='complete';e.cr.atomic_json(a.output,report)
 parent=json.loads((ROOT/'reasoning/cycle2/trial_006_parent_full.json').read_text())
 metric=compare({'rows':parent['rows'],'protocol':PROTOCOL},report,fresh=False,controls_preserved=False)
 e.cr.atomic_json(a.output.with_name(a.output.stem+'_comparison.json'),metric)
 print(json.dumps(metric,indent=2))
if __name__=='__main__':main()
