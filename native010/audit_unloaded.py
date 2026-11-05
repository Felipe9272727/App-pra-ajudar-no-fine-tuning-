"""Audit checkpoint tensors absent from both evaluated autoregressive runtimes."""
from pathlib import Path
import sys,json,hashlib,math
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'native010';sys.path.insert(0,str(ROOT))
from native010.audit_all import inspect_tensor,matrix_diagnostics,torch
from safetensors import safe_open

def main():
 torch.set_num_threads(1)
 rows=[json.loads(s) for s in (HERE/'parameters.jsonl').read_text().splitlines()]
 donors={r['original_donor'] for r in rows if r.get('original_donor')};loaded={r['name'] for r in rows}
 out={'purpose':'Raw checkpoint inventory in addition to the complete actual-loaded-model audit','not_a_weight_edit':True,'original_unloaded':[],'port_unloaded':[],'files':{}}
 vectors={}
 original=ROOT/'upstream/model.safetensors-00001-of-00001.safetensors';port=ROOT/'sensenova_port/model.safetensors'
 with safe_open(original,framework='pt') as source,safe_open(port,framework='pt') as scaffold:
  for key in source.keys():
   if key in donors:continue
   w=source.get_tensor(key);r={'name':key,**inspect_tensor(w)}
   if w.ndim>=2:v,d=matrix_diagnostics(w);vectors[key]=v;r['matrix_diagnostics']=d
   out['original_unloaded'].append(r)
  for key in scaffold.keys():
   if key in loaded:continue
   w=scaffold.get_tensor(key)
   if key in source.keys():
    ref=source.get_tensor(key);assert torch.equal(w,ref),key
    out['port_unloaded'].append({'name':key,'numel':w.numel(),'bitwise_equal_to_scanned_original':True})
   else:out['port_unloaded'].append({'name':key,**inspect_tensor(w)})
  out['raw_original_tensors']=len(source.keys());out['raw_original_values']=sum(math.prod(source.get_slice(k).get_shape()) for k in source.keys())
  out['raw_port_tensors']=len(scaffold.keys());out['raw_port_values']=sum(math.prod(scaffold.get_slice(k).get_shape()) for k in scaffold.keys())
 out['additional_unique_values_scanned']=sum(x['numel'] for x in out['original_unloaded'])
 out['nonfinite_additional_values']=sum(x['nan']+x['inf'] for x in out['original_unloaded'])
 for path in [original,port]:
  with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
  out['files'][str(path.relative_to(ROOT))]={'bytes':path.stat().st_size,'sha256':digest}
 out['explanation']='The raw Qwen file also stores multi-token-prediction (mtp.*) weights. Neither the standard original autoregressive loader nor our evaluated hybrid instantiates them. They remain preserved and were scanned separately; this is not a missing thinking module or a cause uniquely assigned to errors.'
 torch.save(vectors,HERE/'unloaded_row_column_norms.pt')
 (HERE/'unloaded_weights.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({k:v for k,v in out.items() if k not in ['original_unloaded','port_unloaded']}))
if __name__=='__main__':main()
