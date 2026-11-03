"""Exact replay of the final decoder MLP for cheap candidate screening.

Only the LAST physical layer's down projection changes. Its inputs and its
residual are independent of that matrix in teacher-forced full-sequence runs.
Full-shaped BF16 tensors preserve GEMM shape and residual-add rounding.
Final generation validation still executes the entire model, with its loops.
"""
from common import *


@torch.inference_mode()
def build_cache(model,tok,rows,path,anchors=False):
    if path.exists():
        cache=torch.load(path,weights_only=True)
        assert cache['data_sha256']==DATA_HASH and cache['anchors']==anchors
        return cache
    captures={};layer=model.model.language_model.layers[31]
    def xhook(module,inputs):captures['x']=inputs[0].detach().clone()
    def rhook(module,inputs):captures['residual']=inputs[0].detach().clone()
    handles=[layer.mlp.down_proj.register_forward_pre_hook(xhook),
             layer.post_attention_layernorm.register_forward_pre_hook(rhook)]
    buckets=collections.defaultdict(list)
    for index,row in enumerate(rows):
        if anchors:
            ids=tok(row,return_tensors='pt',add_special_tokens=False)['input_ids']
            n=min(8,ids.shape[1]-1);targets=ids[0,-n:]
        else:
            ids=prompt_ids(tok,row['question']);target=tok.encode(row['answer'],add_special_tokens=False)
            ids=torch.cat([ids,torch.tensor([target])],1)
            targets=torch.tensor(target+[tok.eos_token_id])
        buckets[ids.shape[1]].append((index,row,ids,targets))
    batches=[];max_delta=0.
    for bucket in buckets.values():
        for offset in range(0,len(bucket),4):
            batch=bucket[offset:offset+4]
            keep=max(len(item[3])+(1 if anchors else 0) for item in batch)
            captures.clear()
            logits=model(input_ids=torch.cat([item[2] for item in batch]),
                use_cache=False,logits_to_keep=keep).logits
            x=captures['x'];residual=captures['residual']
            hidden=residual+F.linear(x,layer.mlp.down_proj.weight)
            replay=model.lm_head(model.model.language_model.norm(hidden)[:,-keep:])
            error=float((logits.float()-replay.float()).abs().max());max_delta=max(max_delta,error)
            assert error==0.,('Final-MLP replay must be bit exact',error)
            batches.append({'x':x,'residual':residual,'keep':keep,
                'items':[{'index':idx,'id':row['id'] if not anchors else str(idx),
                          'targets':targets} for idx,row,ids,targets in batch]})
            print('CACHE',path.name,len(batches),'max_logit_delta',max_delta,flush=True)
    for handle in handles:handle.remove()
    cache={'data_sha256':DATA_HASH,'anchors':anchors,'rows':len(rows),'batches':batches,
        'max_replay_logit_delta':max_delta,'recipe':RECIPE}
    torch.save(cache,path)
    return cache


@torch.inference_mode()
def score_cache(model,cache):
    layer=model.model.language_model.layers[31]
    rows=[None]*cache['rows'];anchors=cache['anchors']
    for batch in cache['batches']:
        hidden=batch['residual']+F.linear(batch['x'],layer.mlp.down_proj.weight)
        logits=model.lm_head(model.model.language_model.norm(hidden)[:,-batch['keep']:]).float()
        for b,item in enumerate(batch['items']):
            targets=item['targets']
            values=logits[b,-len(targets)-1:-1] if anchors else logits[b,-len(targets):]
            losses=F.cross_entropy(values,targets,reduction='none')
            if anchors:
                rows[item['index']]={'nll':float(losses.mean()),'tokens':len(targets)}
            else:
                rows[item['index']]={'id':item['id'],'answer_nll':float(losses[:-1].mean()),
                    'eos_nll':float(losses[-1]),
                    'teacher_forced_answer_token_accuracy':float((values[:-1].argmax(-1)==targets[:-1]).float().mean())}
    if anchors:return {'mean_nll':statistics.mean(x['nll'] for x in rows),'rows':rows}
    return {'mean_answer_nll':statistics.mean(x['answer_nll'] for x in rows),
        'mean_eos_nll':statistics.mean(x['eos_nll'] for x in rows),
        'mean_answer_token_accuracy':statistics.mean(x['teacher_forced_answer_token_accuracy'] for x in rows),'rows':rows}
