"""Three sequential closed-form writes to the existing last MLP matrix.

The first wrong next-token margin is corrected; earlier correct prefixes and
natural text are preservation constraints. No gradient or runtime adapter.
"""
from common import *
from likelihood_cache import build_cache,score_cache
from protocol import first_error
from publish_progress import publish


@torch.inference_mode()
def regression_step(model,traincache,anchorcache,base):
    layer=model.model.language_model.layers[31].mlp.down_proj
    norm=model.model.language_model.norm
    normscale=1+norm.weight.float()
    xs=[];ys=[];wrong=0;positions=0;preserved=0
    cfg=DATA['protocol']
    for cache in [traincache,anchorcache]:
        for batch in cache['batches']:
            hidden=batch['residual']+F.linear(batch['x'],layer.weight)
            logits=model.lm_head(norm(hidden)[:,-batch['keep']:]).float()
            for b,item in enumerate(batch['items']):
                targets=item['targets'];n=len(targets)
                if cache['anchors']:
                    x=batch['x'][b,-n-1:-1].float()
                    xs.append(x);ys.append(torch.zeros(n,base.shape[0]))
                    preserved+=n
                    continue
                values=logits[b,-n:];h=hidden[b,-n:].float();x=batch['x'][b,-n:].float()
                pred=values.argmax(-1);j=first_error(pred.tolist(),targets.tolist())
                # Teacher-forced first-error prefix; full cached generation is validated separately.
                keep=n if j is None else j+1
                y=torch.zeros(keep,base.shape[0])
                positions+=n;preserved+=keep-(j is not None)
                if j is not None:
                    wrong+=1
                    v=(model.lm_head.weight[targets[j]].float()-model.lm_head.weight[pred[j]].float())*normscale
                    v-=h[j]*(torch.dot(v,h[j])/h[j].square().sum().clamp_min(1e-8))
                    rms=(h[j].square().mean()+norm.eps).sqrt()
                    gap=(values[j,pred[j]]-values[j,targets[j]]+cfg['margin']).clamp_min(0)
                    delta=gap*rms*v/v.square().sum().clamp_min(1e-8)
                    delta*=min(1.,float(cfg['hidden_residual_cap']*h[j].norm()/delta.norm().clamp_min(1e-8)))
                    y[j]=delta
                xs.append(x[:keep]);ys.append(y)
    x=torch.cat(xs).T.contiguous();y=torch.cat(ys).T.contiguous()
    # Weight anchors after per-column normalization, so their weight survives scaling.
    norms=x.norm(dim=0).clamp_min(1e-5);x=x/norms;y=y/norms
    # Anchor batches were appended last, each with exactly n positions.
    nanchors=sum(len(item['targets']) for batch in anchorcache['batches'] for item in batch['items'])
    x[:,-nanchors:]*=cfg['anchor_weight']**.5
    y[:,-nanchors:]*=cfg['anchor_weight']**.5
    gram=x.T@x
    delta=y@torch.linalg.solve(gram+cfg['ridge']*torch.eye(gram.shape[0]),x.T)
    delta*=min(1.,float(cfg['step_norm_cap']*base.norm()/delta.norm().clamp_min(1e-8)))
    cumulative=layer.weight.float()+delta-base
    cumulative*=min(1.,float(cfg['cumulative_norm_cap']*base.norm()/cumulative.norm().clamp_min(1e-8)))
    written=(base+cumulative).to(layer.weight.dtype)
    assert torch.isfinite(written).all()
    layer.weight.copy_(written)
    return {'first_wrong_examples':wrong,'training_token_positions':positions,
        'regression_columns':x.shape[1],'preservation_columns':preserved,
        'anchor_positions':nanchors,'ridge':cfg['ridge'],
        'cumulative_relative_norm':float((written.float()-base).norm()/base.norm())}


@torch.inference_mode()
def develop():
    assert not (HERE/'frozen.json').exists()
    model=load_hybrid();tok=tokenizer()
    base=model.model.language_model.layers[31].mlp.down_proj.weight.float().clone()
    update_status(status='collecting_exact_training_cache',phase='cycle2_closed_form',model_process_active=True)
    traincache=build_cache(model,tok,DATA['train'],HERE/'train_cache.pt')
    devcache=build_cache(model,tok,DATA['development'],HERE/'development_cache.pt')
    anchorcache=build_cache(model,tok,DATA['anchors'],HERE/'anchor_cache.pt',True)
    basegen=generate_rows(model,tok,DATA['development'],HERE/'development_generation_baseline.json',
        {'variant':'active_hybrid_baseline','recipe':RECIPE})
    baseline={'answer':score_cache(model,devcache),'anchors':score_cache(model,anchorcache),
        'generation':{k:basegen[k] for k in ['exact_correct','content_correct','total']},
        'architecture':architecture_check(model)}
    atomic_json(HERE/'development_baseline.json',baseline)
    atomic_json(HERE/'screening_cache_check.json',{'max_logit_delta':max(c['max_replay_logit_delta'] for c in [traincache,devcache,anchorcache]),'final_generation_uses_full_model':True})
    archive={'data_sha256':DATA_HASH,'candidates':[],'heldout_used':False,'recipe':RECIPE}
    for step in range(1,DATA['protocol']['rounds']+1):
        key=f'candidate_{step:02d}'
        update_status(status='editing_weights',evaluating_candidate=key,round=step)
        stats=regression_step(model,traincache,anchorcache,base)
        patch={'dense_weight':model.model.language_model.layers[31].mlp.down_proj.weight.detach().clone(),
            'data_sha256':DATA_HASH,'recipe':RECIPE,'step':step,'layer':31,
            'target':'mlp.down_proj.weight','runtime_adapter':False,'backward_passes':0}
        path=HERE/f'{key}.pt';torch.save(patch,path)
        written=apply_edit(model,path)
        generation=generate_rows(model,tok,DATA['development'],HERE/f'development_generation_{key}.json',
            {'variant':key,'patch_sha256':file_hash(path),'recipe':RECIPE,'weight_write':written})
        scored=score_cache(model,devcache);anchors=score_cache(model,anchorcache)
        correct=generation['exact_correct']>basegen['exact_correct']
        preserves=anchors['mean_nll']<=baseline['anchors']['mean_nll']*1.1
        candidate={'id':key,'step':step,'family':'iterative_first_error','patch':str(path.relative_to(ROOT)),
            'patch_sha256':file_hash(path),'ridge':DATA['protocol']['ridge'],
            'status':'development_complete','development':scored,'anchor':anchors,
            'development_generation':{k:generation[k] for k in ['exact_correct','content_correct','total']},
            'passes_development_generation':correct,'passes_anchor':preserves,
            'validation_eligible':correct and preserves,'weight_write':written,'training':stats}
        archive['candidates'].append(candidate)
        atomic_json(HERE/'archive.json',archive);atomic_json(HERE/f'round_{step:03d}.json',candidate)
        atomic_json(HERE/'fit_metadata.json',{'method':'iterative first-error RMSNorm margin + closed-form ridge; dense BF16 writes','training_examples':len(DATA['train']),'backward_passes':0,'rounds_completed':step,'data_sha256':DATA_HASH,'architecture':architecture_check(model),'protocol':DATA['protocol']})
        update_status(status='round_checkpointed',rounds_completed=step,candidates_fitted=step)
        publish(f'round {step} weights and development decision')
        print('ROUND',step,'exact',generation['exact_correct'],'baseline',basegen['exact_correct'],'eligible',candidate['validation_eligible'],flush=True)
    eligible=sorted([c for c in archive['candidates'] if c['validation_eligible']],
        key=lambda c:(-c['development_generation']['exact_correct'],c['development']['mean_answer_nll']))[:2]
    atomic_json(HERE/'validation_queue.json',{'candidate_ids':[c['id'] for c in eligible],
        'criterion':DATA['protocol']['selection'],'heldout_used':False})
    update_status(status='awaiting_validation',model_process_active=False,
        validation_queue=[c['id'] for c in eligible],evaluating_candidate=None)
    publish('development complete and validation queue')

if __name__=='__main__':develop()
