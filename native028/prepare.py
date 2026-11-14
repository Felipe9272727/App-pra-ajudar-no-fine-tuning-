"""Read-only parent retention cache, zero-delta parity and no-update backward audit."""
from core import *


def main():
    torch.set_num_threads(4)
    assert not (H/'reports/preflight.json').exists(),'Inspect previous preflight before repeating'
    model,tok,parent,meta=tr.load();del parent
    before={n:tensor_hash(p) for n,p in model.named_parameters()};assert len(before)==699
    rows=read('data/train_code.json')+read('data/train_general.json')+read('data/train_tools.json')
    sizes=[]
    for row in rows:
        for think in [False,True]:
            ids,gold,prefix=encode(tok,row,think)
            sizes.append({'id':row['id'],'thinking':think,'input_tokens':ids.shape[1],
                'prefix_tokens':prefix,'target_tokens':len(gold)})
    save('reports/token_audit.json',{'paired_problems':len(rows),'supervised_views':len(sizes),
        'target_tokens_per_epoch':sum(r['target_tokens'] for r in sizes),'max_training_input':max(r['input_tokens'] for r in sizes),'rows':sizes})
    anchors=read('data/anchors.json');cache={}
    with torch.no_grad():
        for row in anchors:
            ids,gold,_=encode(tok,row,False);h=hidden(model,ids,gold)
            logits=F.linear(h,model.get_output_embeddings().weight).float()
            logp=F.log_softmax(logits,dim=-1);lp,idx=logp.topk(read('config.json')['anchor_topk'],dim=-1)
            cache[row['id']]={'indices':idx.cpu(),'logp':lp.cpu(),'other':(1-lp.exp().sum(-1)).clamp_min(1e-8).cpu()}
            print('ANCHOR028',row['id'],len(gold),flush=True)
    assert all(tensor_hash(p)==before[n] for n,p in model.named_parameters())
    torch.save(cache,H/'data/parent_anchor_top32.pt.bin')
    del cache,h,logits,logp,lp,idx;gc.collect()
    example=rows[0];ids,gold,_=encode(tok,example,True)
    with torch.no_grad():reference=F.linear(model.model(input_ids=ids,use_cache=False).last_hidden_state[0,-1:],model.get_output_embeddings().weight).float().clone()
    materialize(model);model.requires_grad_(False);descriptors=install(model,read('config.json')['rank'])
    with torch.no_grad():observed=F.linear(model.model(input_ids=ids,use_cache=False).last_hidden_state[0,-1:],model.get_output_embeddings().weight).float()
    assert torch.equal(reference,observed),'Zero adapter changed initial logits'
    assert all(tensor_hash(p)==before[n] for n,p in base_parameters(model).items())
    native={n:p for n,p in model.named_parameters() if n in controls()};factors={n:p for n,p in model.named_parameters() if '.lora_' in n}
    model.train();model.model.visual.eval();torch.set_grad_enabled(True);wrapper=CheckpointVisits(model)
    # Use longest teaching view, not just a conveniently short program.
    longest=max(sizes,key=lambda r:r['input_tokens']);row=next(r for r in rows if r['id']==longest['id'])
    ids,gold,_=encode(tok,row,longest['thinking']);v=sft_loss(model,ids,gold);v.backward()
    eligible={**native,**factors};assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in eligible.values())
    assert all(wrapper.calls[(i,j)]>=2 for i in range(4,28) for j in [0,1])
    assert all(tensor_hash(p)==before[n] for n,p in base_parameters(model).items())
    report={'status':'no_optimizer_update_preflight_passed','parent_sha256':tr.PARENT_HASH,
        'zero_adapter_last_logits_bit_equal':True,'all699_base_hashes_unchanged':True,
        'both_actual_visits_recomputed':True,'factor_modules':len(descriptors),
        'factor_tensors':len(factors),'factor_values':sum(p.numel() for p in factors.values()),
        'native_tensors':len(native),'native_values':sum(p.numel() for p in native.values()),
        'gradient_present':len(eligible),'nonzero_gradients':sum(bool(p.grad.count_nonzero()) for p in eligible.values()),
        'zero_A_gradients_expected_at_zero_B':True,'longest_example':longest,'loss':float(v.detach()),
        'architecture':meta['architecture'],'all699_parent_hashes':before,'descriptors':descriptors,**memory()}
    save('reports/preflight.json',report)
    wrapper.close();del wrapper,model,eligible,native,factors,v;gc.collect()
    print('PREPARE028_COMPLETE',report['factor_values'],report['native_values'],report['peak_rss_kb'],flush=True)


if __name__=='__main__':main()
