"""Causality, cache-window alignment, and zero-padded convolution contracts."""
import json
from pathlib import Path
import torch
import torch.nn.functional as F
from native_runtime import window_mask

torch.set_num_threads(8)
torch.set_grad_enabled(False)
torch.manual_seed(3401)


def main():
    hidden=torch.zeros(1,300,16,dtype=torch.bfloat16)
    full=window_mask(None,hidden,None,None,256)
    allowed=full[0,0]==0
    for i in range(300):
        expected=torch.zeros(300,dtype=torch.bool)
        expected[max(0,i-255):i+1]=True
        assert torch.equal(allowed[i],expected)
    class Cache:
        def get_seq_length(self,index):return 299
    class View:
        cache=Cache()
        virtual=7
    single=window_mask(None,hidden[:,:1],torch.tensor([[299]]),View(),256)
    assert torch.equal(single[0,0,0],full[0,0,-1])
    x=torch.randn(1,16,330,dtype=torch.bfloat16)
    w4=torch.randn(16,1,4,dtype=torch.bfloat16)
    w7=F.pad(w4,(3,0))
    y4=F.conv1d(x,w4,groups=16,padding=3)[...,:330]
    y7=F.conv1d(x,w7,groups=16,padding=6)[...,:330]
    delta=(y4.float()-y7.float()).abs().max().item()
    assert delta<=0.0625
    data={'window':256,'full_context_tokens':300,
          'causal_rows_checked':300,'last_row_allowed_keys':int(allowed[-1].sum()),
          'cached_last_row_matches_full':True,
          'zero_padded_kernel7_max_delta':delta,
          'note':'Operator contracts, not a long-context quality benchmark.'}
    (Path(__file__).resolve().parent/'runtime_checks.json').write_text(json.dumps(data,indent=2))
    print(json.dumps(data))


if __name__=='__main__':main()
