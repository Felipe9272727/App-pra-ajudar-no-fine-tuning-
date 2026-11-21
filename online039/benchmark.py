"""Fixed CPU/CUDA parity probes, not a general intelligence benchmark."""
import sys,json,argparse,collections,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(Path(__file__).parent/'space')]
from runtime import Runtime, PACK_SHA, torch
from local_cpu.sandbox import evaluate
CASES=[{'id':'arithmetic','prompt':'Quanto é 2 + 2? Responda apenas o número.','budget':8},
 {'id':'code_square','prompt':'Write only Python function solve(xs). Return the sum of squares of the even integers in xs. No imports.','budget':64,'cases':[{'args':[[1,2,3,4]],'expected':20},{'args':[[]],'expected':0},{'args':[[-2,3,0]],'expected':4}]}]
def main():
 p=argparse.ArgumentParser();p.add_argument('--assets',required=True);p.add_argument('--device',choices=['cpu','cuda'],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--reference',type=Path);p.add_argument('--code-budget',type=int,default=64);a=p.parse_args();assert not a.output.exists(),'Preserve previous reports'
 if a.device=='cuda' and not torch.cuda.is_available():raise RuntimeError('CUDA GPU unavailable; no speed claim')
 torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;r=Runtime(a.assets,a.device);counts=collections.Counter();hooks=[]
 for i,layer in enumerate(r.text.layers):hooks.append(layer.register_forward_hook(lambda m,inp,out,i=i:counts.update([i])))
 rows=[]
 for row in CASES:
  budget=a.code_budget if 'cases' in row else row['budget']
  counts.clear();out=r.generate([{'role':'user','content':row['prompt']}],budget);expected={i:(2 if 4<=i<28 else 1)*len(out['tokens']) for i in range(32)};assert dict(counts)==expected,(counts,expected)
  out.update(id=row['id'],loop_visit_counts=dict(counts),prompt=row['prompt'],budget=budget)
  if 'cases'in row:out['evaluation']=evaluate(out['text'],row)
  else:out['correct']=out['text'].strip()=='4'
  rows.append(out)
 for h in hooks:h.remove()
 report={'device':a.device,'torch':torch.__version__,'tensor_count':len(r.audit),'weights_sha256':r.manifest['source_checkpoint_sha256'],'pack_sha256':PACK_SHA,'tensor_audit_sha256':hashlib.sha256(json.dumps(r.audit,sort_keys=True).encode()).hexdigest(),'rows':rows,'general_benchmark':False,'speedup_claim':False}
 if a.reference:
  ref=json.loads(a.reference.read_text());assert ref['tensor_audit_sha256']==report['tensor_audit_sha256'];assert [x['prompt'] for x in ref['rows']]==[x['prompt'] for x in rows];assert all(y.get('budget', row['budget']) == x['budget'] for x,y,row in zip(rows,ref['rows'],CASES));report['parity']=[{'id':x['id'],'same_tokens':x['tokens']==y['tokens'],'CPU_seconds':y['seconds'],'candidate_seconds':x['seconds']} for x,y in zip(rows,ref['rows'])]
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'output':str(a.output),'rows':[(r['id'],r.get('correct',r.get('evaluation',{}).get('passed'))) for r in rows]}))
if __name__=='__main__':main()
