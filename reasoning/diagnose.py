"""Measure actual per-visit states on observed errors and successful guards."""
import collections
import json
import math
from common import *

ERRORS = ['prefix_sums','rotate_right','longest_run']
GUARDS = ['sum_abs','palindrome','binary_search']
ACTIVE = [i for i in range(4,28) if i not in set(range(8,12))|set(range(20,24))]


@torch.inference_mode()
def main():
    assert not (HERE/'diagnostic.json').exists(), 'Saved diagnostic exists; do not duplicate'
    model,tok,parent,meta = load()
    historical={r['id']:r for r in json.loads((e.HERE/'best_metrics.json').read_text())['rows']}
    traces={};report={'status':'running','rows':[],'parent_sha256':PARENT_HASH,
        'errors':ERRORS,'guards':GUARDS,'backward_passes':0,
        'solutions_or_positive_targets_in_prompts':False}
    for task in tasks(ERRORS+GUARDS):
        states=[];pending={};stats=collections.defaultdict(list);meanabs={};handles=[]
        for index in ACTIVE:
            def pre(module,inputs,index=index):
                x=inputs[0][0,-1].detach().float()
                visit=model.model.language_model.layers[index]._last_native_visit
                key=(index,visit)
                meanabs[key]=meanabs.get(key,torch.zeros_like(x))+x.abs()
                if visit==0:
                    pending[index]=x.clone()
                else:
                    first=pending.pop(index)
                    ratio=float((x-first).norm()/first.norm().clamp_min(1e-8))
                    cosine=float(torch.nn.functional.cosine_similarity(x,first,dim=0))
                    stats[index].append((ratio,cosine))
            handles.append(model.model.language_model.layers[index].mlp.down_proj.register_forward_pre_hook(pre))
        handles.append(model.model.language_model.layers[31].mlp.down_proj.register_forward_pre_hook(
            lambda module,inputs:states.append(inputs[0][0,-1].detach().float().clone())))
        try:
            ids=e.cr.prompt(tok,task['prompt']);torch.manual_seed(0)
            result=model.generate(input_ids=ids,max_new_tokens=160,use_cache=True,do_sample=False,
                                  pad_token_id=tok.eos_token_id)
        finally:
            for h in handles:h.remove()
        own=result[0,ids.shape[1]:].tolist();text=tok.decode(own,skip_special_tokens=True)
        assert text==historical[task['id']]['output'],'Parent replay drift; stop before editing'
        scored=evaluate(text,task)
        assert scored['case_passed']==historical[task['id']]['case_passed']
        traces[task['id']]={'states':torch.stack(states),'token_ids':torch.tensor(own),
                                'output':text}
        row={'id':task['id'],'group':'error' if task['id'] in ERRORS else 'guard',
             'output':text,**scored,'layers':{}}
        for i in ACTIVE:
            values=stats[i]
            row['layers'][str(i)]={'mean_log1p_visit_drift':sum(math.log1p(x[0]) for x in values)/len(values),
                'mean_cosine':sum(x[1] for x in values)/len(values),'observations':len(values),
                'top_active_input_coordinates':{str(v):meanabs[(i,v)].topk(16).indices.tolist() for v in [0,1]}}
        report['rows'].append(row);save('diagnostic_progress.json',report)
        tensor_checkpoint(traces,HERE/'traces.pt')
        print('DIAGNOSED',task['id'],scored['passed'],scored['total'],flush=True)
    ranking=[]
    for i in ACTIVE:
        means={g:sum(r['layers'][str(i)]['mean_log1p_visit_drift'] for r in report['rows'] if r['group']==g)/3
               for g in ['error','guard']}
        ranking.append({'layer':i,'contrast':means['error']-means['guard'],**means})
    ranking.sort(key=lambda r:(-r['contrast'],r['layer']))
    report.update(status='complete',ranking=ranking,target_layers=[r['layer'] for r in ranking[:3]],
        control_layers=[r['layer'] for r in ranking[-3:]],
        interpretation='Correlation and intervention candidates; not dedicated reasoning neurons',
        traces_sha256=e.cr.file_hash(HERE/'traces.pt'))
    save('diagnostic.json',report)
    print('DIAGNOSTIC_COMPLETE',report['target_layers'],report['control_layers'],flush=True)


if __name__=='__main__':main()
