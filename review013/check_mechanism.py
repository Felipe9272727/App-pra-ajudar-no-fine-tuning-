"""Real-weight safety and cache checks before opening validation outputs."""
import gc,json
from review_runtime import *
from native010.native_runtime import tensor_hash

@torch.inference_mode()
def main():
    verify_frozen();report={'variants':{}}
    model,tok,meta,_=load_variant('parent')
    before={n:tensor_hash(p) for n,p in model.named_parameters()}
    ids=e.cr.prompt(tok,'Write function solve(xs) returning the length of xs. Return only the function.')
    baseline=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits.detach().clone()
    zeros=torch.load(HERE/'checkpoints'/'joint.pt',weights_only=True)
    zeros['output_map']=torch.zeros_like(zeros['output_map'])
    installed=Installed(model,zeros)
    after=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits
    assert torch.equal(baseline,after),'zero adapter changed logits'
    installed.close();report['zero_adapter_logits_bit_exact']=True
    assert all(tensor_hash(dict(model.named_parameters())[n])==h for n,h in before.items())
    for kind in ['loop','joint']:
        patch=torch.load(HERE/'checkpoints'/(kind+'.pt'),weights_only=True)
        installed=Installed(model,patch)
        check=e.cr.cache_check(model,tok,2)
        full=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits.float()
        same_prefill=model(input_ids=ids,use_cache=False,logits_to_keep=1).logits.float()
        assert torch.equal(full,same_prefill),'request history leaked'
        delta=float((full-baseline.float()).abs().max())
        assert torch.isfinite(full).all()
        assert all(tensor_hash(dict(model.named_parameters())[n])==h for n,h in before.items())
        report['variants'][kind]={'cache_probe':check,'request_repeat_bit_exact':True,
                 'all_parent_tensors_unchanged':len(before),'max_logit_delta_vs_parent':delta,
                 'mechanism':installed.stats()}
        installed.close()
    report['status']='complete';save('mechanism.json',report);print(json.dumps(report,indent=2))

if __name__=='__main__':main()
