"""Actual all-text backward preflight; NO optimizer or parameter update."""
import json,time
from train_runtime import *
def main():
    m,t,meta,eligible,wrapper=load_trainable()
    before={n:tensor_hash(p) for n,p in m.named_parameters()}
    row={'prompt':'Write Python function f(x) returning x + 1. Return only the function.',
         'solution':'def f(x):\n    return x + 1\n'}
    ids,gold=encode(t,row)
    with torch.no_grad():
        m.eval()
        full=m(input_ids=ids,use_cache=False,logits_to_keep=1).logits.float()
        hidden=m.model(input_ids=ids,use_cache=False).last_hidden_state[:,-1:]
        direct=m.lm_head(hidden).float()
        assert torch.equal(full,direct),'Training path differs from inference path'
    m.train();started=time.monotonic();value=loss(m,ids,gold);value.backward()
    coverage=[]
    for name,p in eligible.items():
        grad=p.grad
        coverage.append({'name':name,'numel':p.numel(),'gradient_present':grad is not None,
              'gradient_nonzero':bool(grad is not None and grad.count_nonzero()),
              'gradient_finite':bool(grad is None or torch.isfinite(grad).all()),'dtype':str(p.dtype)})
    assert all(r['gradient_finite'] for r in coverage)
    assert all(tensor_hash(p)==before[n] for n,p in m.named_parameters()),'Preflight changed weights'
    report={'status':'backward_passed_no_weight_update','loss':float(value.detach()),'seconds':time.monotonic()-started,
        'eligible_tensors':len(coverage),'eligible_parameters':sum(r['numel'] for r in coverage),
        'gradient_present_tensors':sum(r['gradient_present'] for r in coverage),
        'nonzero_gradient_tensors':sum(r['gradient_nonzero'] for r in coverage),
        'all_parent_weights_unchanged':True,'forward_path_bit_exact':True,'optimizer_steps':0,
        'checkpoint_calls':{str(k):v for k,v in wrapper.calls.items()},'coverage':coverage,
        'memory_peak_bytes':int(Path('/sys/fs/cgroup/memory.peak').read_text())}
    save('backward_smoke.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ['coverage','checkpoint_calls']},indent=2))
if __name__=='__main__':main()
