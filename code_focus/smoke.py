"""Technical check that sparse patches actually modify the existing tensor."""
import sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'code_rsi'))
from selectivity import choose_channels,write_columns
from checkpoint_io import tensor_checkpoint
import torch

def main():
 torch.set_grad_enabled(False)
 weight=torch.arange(8*256,dtype=torch.float32).reshape(8,256).bfloat16();before=weight.clone()
 indices=torch.tensor([0,5,10,20]);columns=(weight.index_select(1,indices).float()*1.15).bfloat16()
 write_columns(weight,indices,columns)
 assert torch.equal(weight.index_select(1,indices),columns)
 keep=torch.tensor([i for i in range(256) if i not in indices.tolist()])
 assert torch.equal(weight.index_select(1,keep),before.index_select(1,keep))
 assert not torch.equal(weight,before)
 with tempfile.TemporaryDirectory() as folder:
  p=Path(folder)/'new/checkpoints/patch.pt';tensor_checkpoint({'indices':indices,'columns_weight':columns},p)
  saved=torch.load(p,weights_only=True);write_columns(weight,saved['indices'],before.index_select(1,indices))
  assert torch.equal(weight,before)
 print('FOCUSED_EXISTING_WEIGHT_WRITE_AND_RESTORE_OK',flush=True)
if __name__=='__main__':main()
