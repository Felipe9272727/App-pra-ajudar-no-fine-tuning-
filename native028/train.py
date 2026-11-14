"""Two fixed epochs: paired thinking views, native controllers and parent retention."""
import argparse
from core import *


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    verify_frozen();cfg=read('config.json');torch.set_num_threads(4);torch.manual_seed(cfg['seed'])
    rolling=Path('/dev/shm/liquid-native028/rolling_sft.pt');journal=H/'steps.jsonl'
    assert not (H/'checkpoints/sft_final/manifest.json').exists(),'Completed SFT must not be repeated'
    assert args.resume or not (rolling.exists() or journal.exists()),'Inspect partial state before resuming'
    model,tok,meta,before,descriptors,native,factors,baseline,masters,wrapper=load_trainable()
    assert before==read('reports/preflight.json')['all699_parent_hashes']
    rows=read('data/train_code.json')+read('data/train_general.json')+read('data/train_tools.json');assert len(rows)==48
    anchors=read('data/anchors.json');cache=torch.load(H/'data/parent_anchor_top32.pt.bin',weights_only=True)
    opt=make_optimizer(factors,masters);started=time.monotonic();step=seen=anchor_seen=0;epochs=[];last_entry={};ever=set()
    if args.resume:
        state=torch.load(rolling,weights_only=True);assert state['parent_sha256']==tr.PARENT_HASH
        with torch.no_grad():
            for n,p in factors.items():p.copy_(state['factors'][n])
            for n,p in native.items():p.copy_(state['native'][n])
            for n,p in masters.items():p.copy_(state['masters'][n])
        opt.load_state_dict(state['optimizer']);torch.set_rng_state(state['rng']);step=state['step']
        extra=state['extra'];seen=extra['sft_tokens'];anchor_seen=extra['anchor_tokens'];epochs=extra['epochs'];last_entry=extra['last_entry'];ever=set(extra['ever_nonzero'])
        lines=[json.loads(x) for x in journal.read_text().splitlines()] if journal.exists() else []
        if len(lines)==step-1:
            with journal.open('a') as f:f.write(json.dumps(last_entry)+'\n')
        assert len(lines) in [step,0] and (step==0 or len(lines)==step)
        del state;gc.collect();print('RESUMED028_SFT',step,flush=True)
    else:
        export(model,native,factors,baseline,masters,opt,before,descriptors,'initial_factors',0)
    def save_work():
        state=payload(model,native,factors,masters,opt,'sft_working',step,{
            'sft_tokens':seen,'anchor_tokens':anchor_seen,'epochs':epochs,'last_entry':last_entry,'ever_nonzero':sorted(ever)})
        tmp=rolling.with_suffix('.tmp');torch.save(state,tmp);tmp.replace(rolling)
    for epoch in [1,2]:
        order=torch.randperm(len(rows),generator=torch.Generator().manual_seed(cfg['seed']+epoch)).tolist()
        for position,index in enumerate(order):
            target_step=(epoch-1)*len(rows)+position+1
            if target_step<=step:continue
            factor=target_step/cfg['warmup_steps'] if target_step<=cfg['warmup_steps'] else cfg['final_lr_fraction']+(1-cfg['final_lr_fraction'])*.5*(1+math.cos(math.pi*(target_step-cfg['warmup_steps'])/(cfg['sft_optimizer_steps']-cfg['warmup_steps'])))
            opt.param_groups[0]['lr']=cfg['factor_lr']*factor;opt.param_groups[1]['lr']=cfg['controller_lr']*factor
            clear_grad(opt,native);losses=[];row=rows[index]
            for thinking in [False,True]:
                ids,gold,_=encode(tok,row,thinking);value=sft_loss(model,ids,gold);losses.append(float(value.detach()));(value*.5).backward();seen+=len(gold);del ids,gold,value
            anchor=anchors[(target_step-1)%len(anchors)];ids,gold,_=encode(tok,anchor,False)
            value=anchor_loss(model,ids,gold,cache[anchor['id']]);kl=float(value.detach());(cfg['sft_retention_weight']*value).backward();anchor_seen+=len(gold);del ids,gold,value
            ever.update(n for n,p in {**factors,**native}.items() if p.grad is not None and bool(p.grad.count_nonzero()))
            norm,counts,events=update(model,opt,native,factors,baseline,masters);step=target_step
            last_entry={'step':step,'epoch':epoch,'id':row['id'],'nonthinking_nll':losses[0],
                'thinking_nll':losses[1],'anchor_coarse_KL':kl,'gradient_norm':norm,**counts,
                'trust_projection_events':len(events),'sft_target_tokens':seen,'anchor_tokens':anchor_seen,
                'lr_factor':factor,'seconds':time.monotonic()-started,**memory()}
            save_work()
            with journal.open('a') as f:f.write(json.dumps(last_entry)+'\n')
            status=read('status.json');status.update(status='training_sft_main',optimizer_updates=step,
                sft_updates=step,epoch=epoch,model_process_active=True,parent_weights_changed=False)
            save('status.json',status)
            if step%4==0 or step==1:print('TRAIN028',step,96,row['id'],losses,kl,counts,flush=True)
            gc.collect()
        stage='sft_epoch1' if epoch==1 else 'sft_final'
        if not (H/'checkpoints'/stage/'manifest.json').exists():
            export(model,native,factors,baseline,masters,opt,before,descriptors,stage,step,
                {'sft_tokens':seen,'anchor_tokens':anchor_seen,'ever_nonzero':sorted(ever)})
            epochs.append({'epoch':epoch,'steps':step,'sft_tokens':seen,'anchor_tokens':anchor_seen})
            save_work();save('reports/sft_epochs.json',epochs);print('EPOCH028_SAVED',stage,step,flush=True)
    assert step==96
    assert seen==2*read('reports/token_audit_projected.json')['target_tokens_per_epoch']
    save('reports/sft_training.json',{'status':'two_epochs_complete_pending_native_quality',
        'steps':step,'sft_target_tokens':seen,'anchor_token_presentations':anchor_seen,'paired_problems':48,
        'supervised_views_per_epoch':96,'factor_tensors':len(factors),'native_tensors':len(native),
        'ever_nonzero_gradient_names':sorted(ever),'both_actual_visits_recomputed':all(wrapper.calls[(i,j)]>=2 for i in range(4,28) for j in [0,1]),
        'visit_calls':{str(k):v for k,v in wrapper.calls.items()},'parent_sha256':tr.PARENT_HASH,
        'seconds_descriptive':time.monotonic()-started,**memory()})
    clear_grad(opt,native);wrapper.close();print('SFT028_COMPLETE',step,seen,flush=True)


if __name__=='__main__':main()
