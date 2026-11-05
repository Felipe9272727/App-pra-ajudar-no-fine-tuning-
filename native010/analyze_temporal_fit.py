"""Evaluate the stored calibration objective; no new model generation or tuning."""
from pathlib import Path
import sys,json,hashlib
import torch
from safetensors import safe_open
import torch.nn.functional as F
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'native010'
sys.path.insert(0,str(ROOT))
from native010.native_runtime import SOURCE_LAYERS,CLONES,tensor_hash

def main():
 torch.set_num_threads(1);torch.set_grad_enabled(False)
 patch=torch.load(ROOT/'checkpoints/liquid_patch.pt',weights_only=True)
 parent=torch.load(ROOT/'rsi100/checkpoints/best.pt',weights_only=True)
 audit={r['name']:r for r in map(json.loads,(HERE/'parameters.jsonl').read_text().splitlines())}
 prior={}
 with safe_open(ROOT/'upstream/model.safetensors-00001-of-00001.safetensors',framework='pt') as f:
  for i in range(32):
   if i%4==3:continue
   p=F.pad(f.get_tensor(f'model.language_model.layers.{SOURCE_LAYERS[i]}.linear_attn.conv1d.weight'),(3,0))
   w=patch['convolutions'].get(i,p).clone();w[:,:,:3].copy_(parent['history'][str(i)])
   assert tensor_hash(w)==audit[f'model.language_model.layers.{i}.linear_attn.conv1d.weight']['sha256_values']
   prior[i]=w
 for i,j in CLONES.items():
  if i in prior:prior[i]=prior[j].clone()
 stats=torch.load(HERE/'liquid_statistics.pt',weights_only=True)
 targets=torch.load(HERE/'teacher_targets.pt',weights_only=True)
 fitted=torch.load(HERE/'checkpoints/liquid.pt',weights_only=True)
 out={};before_total=0.;after_total=0.
 for i,s in stats.items():
  w=prior[i][:,0,:].float();v=fitted[f'model.language_model.layers.{i}.linear_attn.conv1d.weight'][:,0,:].float()
  G=s['G']/s['n'];b=s['b']/s['n']
  yy=sum(t[SOURCE_LAYERS[i]].float().square().sum(0) for t in targets.values())/s['n']
  def loss(x):return float((torch.einsum('ck,ckl,cl->c',x,G,x)-2*(b*x).sum(-1)+yy).mean().clamp_min(0))
  a,z=loss(w),loss(v);before_total+=a;after_total+=z
  out[str(i)]={'before_calibration_mse':a,'after_calibration_mse':z}
 result={'used_to_select_weights':False,'same_calibration_inputs':True,'target_storage_dtype':'bfloat16','unlabelled_inputs':19,
  'mean_layer_mse_before':before_total/len(out),'mean_layer_mse_after':after_total/len(out),
  'relative_calibration_mse_reduction':1-after_total/before_total,'per_layer':out,
  'not_a_task_accuracy_or_generalization_result':True}
 (HERE/'temporal_objective.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='per_layer'}))
if __name__=='__main__':main()
