import copy,tempfile,unittest
from pathlib import Path
import torch
import checkpoint as codec

class Model(torch.nn.Module):
    def __init__(self):
        super().__init__();self.model=torch.nn.Module();self.model.language_model=torch.nn.Module()
        self.model.language_model.matrix=torch.nn.Parameter(torch.arange(64).reshape(8,8).to(torch.bfloat16)/10)
        self.model.language_model.gain=torch.nn.Parameter(torch.tensor([.95,.05],dtype=torch.float32))

class Tests(unittest.TestCase):
    def test_exact_bf16_fp32_roundtrip(self):
        base=Model();new=copy.deepcopy(base)
        with torch.no_grad():
            new.model.language_model.matrix.add_(.125);new.model.language_model.gain.copy_(torch.tensor([.9,.1]))
        with tempfile.TemporaryDirectory() as d:
            m=codec.write(d,new,base,'parent');self.assertEqual(m['changed_tensors'],2)
            codec.restore(d,base,'parent')
            for a,b in zip(base.parameters(),new.parameters()):self.assertTrue(torch.equal(a.view(torch.uint8),b.view(torch.uint8)))
    def test_corruption_rejected(self):
        base=Model();new=copy.deepcopy(base)
        with tempfile.TemporaryDirectory() as d:
            m=codec.write(d,new,base,'parent');p=Path(d)/m['parts'][0]['path'];b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
            with self.assertRaises((OSError,AssertionError,EOFError)):codec.restore(d,base,'parent')

if __name__=='__main__':unittest.main()
