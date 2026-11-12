"""Actual two-example shared-loop backward with gradients released; no update."""
import time
from train_runtime import *
from optimizer import BackwardAdafactor

def main():
    model,tok,_,eligible,wrapper=load_trainable()
    before={n:tensor_hash(p) for n,p in model.named_parameters()}
    opt=BackwardAdafactor(eligible,update=False)
    rows=[{'prompt':'Write Python function f(x) returning x + 1. Return only the function.','solution':'def f(x):\n    return x + 1\n'},
          {'prompt':'Write Python function g(x) returning x - 1. Return only the function.','solution':'def g(x):\n    return x - 1\n'}]
    started=time.monotonic();values=[]
    for row in rows:
        ids,gold=encode(tok,row);values.append(loss(model,ids,gold))
    total=torch.stack(values).mean();total.backward()
    assert set(opt.calls)==set(eligible) and set(opt.calls.values())=={1}
    assert all(p.grad is None for p in eligible.values())
    assert all(tensor_hash(p)==before[n] for n,p in model.named_parameters())
    report={'status':'two_example_streaming_backward_passed','parameters':sum(p.numel() for p in eligible.values()),
       'gradient_tensors':len(opt.stats),'nonzero_tensors':sum(r['nonzero'] for r in opt.stats.values()),
       'calls_per_parameter':1,'optimizer_updates':0,'all_parent_weights_unchanged':True,
       'loss':float(total.detach()),'seconds':time.monotonic()-started,
       'memory_peak_bytes':int(Path('/sys/fs/cgroup/memory.peak').read_text()),
       'rss_kb':int(Path('/proc/self/status').read_text().split('VmRSS:')[1].split()[0])}
    save('streaming_smoke.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
