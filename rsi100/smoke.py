"""Tensor proposal and serialization checks on a tiny synthetic checkpoint."""
from pathlib import Path
import sys,tempfile,copy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code_rsi'))
from checkpoint_io import tensor_checkpoint
from mutation import propose
import torch

def main():
 torch.set_grad_enabled(False);torch.manual_seed(100)
 base={'dense_weight':torch.randn(8,32).bfloat16(),'history':{'0':torch.randn(8,1,3).bfloat16()},
  'router_bias':{'4.mhc_attn':torch.randn(8)},'passes':2,'late_gain':.05,'data_sha256':'tiny','round':0}
 before=copy.deepcopy(base);direction=torch.randn(32);directions=[]
 for number in range(1,101):
  child,meta=propose(base,base,direction,number,101)
  assert child['passes'] in [2,3,4] and .01<=child['late_gain']<=.20
  assert torch.isfinite(child['dense_weight']).all() and meta['dense_relative_norm']<=.081
  assert torch.equal(base['dense_weight'],before['dense_weight'])
  assert torch.equal(base['history']['0'],before['history']['0'])
  replay,_=propose(base,base,direction,number,101)
  assert torch.equal(child['dense_weight'],replay['dense_weight'])
  assert torch.equal(child['router_bias']['4.mhc_attn'],replay['router_bias']['4.mhc_attn'])
 with tempfile.TemporaryDirectory() as directory:
  path=Path(directory)/'not-in-git/checkpoints/best.pt';tensor_checkpoint(base,path)
  restored=torch.load(path,weights_only=True)
  assert torch.equal(base['dense_weight'],restored['dense_weight'])
 print('RSI100_PROPOSALS_AND_COLD_CHECKPOINT_OK',flush=True)
if __name__=='__main__':main()
