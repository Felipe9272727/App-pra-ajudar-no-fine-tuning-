"""Bounded TRAIN-only group-relative PPO; genuine reward variance required."""
import argparse
from core import *
from inference import prefix,repeat_fraction,judge,verify_stage


@torch.no_grad()
def sample(model,tok,row,generator):
    cfg=read('config.json');p=prefix(tok,row,True);out=[];old=[];cache=None
    model.eval();start=time.monotonic()
    for i in range(cfg['rl_budget']):
        ids=torch.tensor([p if i==0 else [out[-1]]],dtype=torch.long)
        o=model.model(input_ids=ids,past_key_values=cache,use_cache=True)
        cache=o.past_key_values;h=o.last_hidden_state[0,-1:]
        logits=F.linear(h,model.get_output_embeddings().weight).float()[0]/cfg['rl_temperature']
        lp=F.log_softmax(logits,dim=-1);token=int(torch.multinomial(lp.exp(),1,generator=generator))
        out.append(token);old.append(float(lp[token]))
        del o,h,logits,lp
        if token in cfg['eos_ids']:break
    del cache;gc.collect();model.train();model.model.visual.eval()
    raw=tok.decode(out,skip_special_tokens=True);final=delivered(raw,True);result=judge(final,row)
    ended=bool(out) and out[-1] in cfg['eos_ids'];closed='</think>' in raw
    reward=.75*result['all_passed']+.25*result['passed']/result['total']
    if result['all_passed']:reward-=.05*len(out)/cfg['rl_budget']
    if not closed:reward-=.1
    if not ended and len(out)==cfg['rl_budget']:reward-=.05
    return {'prefix_ids':p,'ids':out,'behavior_logp':old,'raw':raw,'delivered':final,
        'thinking_closed':closed,'ended_eos':ended,'tokens':len(out),'reward':reward,
        'seconds_descriptive_only':time.monotonic()-start,'repeated_8gram_fraction':repeat_fraction(out),**result}


def replay_loss(model,item,advantage):
    cfg=read('config.json');y=torch.tensor(item['ids'],dtype=torch.long)
    ids=torch.tensor([item['prefix_ids']+item['ids'][:-1]],dtype=torch.long)
    old=torch.tensor(item['behavior_logp'],dtype=torch.float32)
    h=hidden(model,ids,y);losses=[];replayed=[];chunk=cfg['head_chunk_tokens']
    def head(x,target,behavior):
        logits=F.linear(x,model.get_output_embeddings().weight).float()/cfg['rl_temperature']
        lp=logits.gather(1,target[:,None])[:,0]-torch.logsumexp(logits,dim=-1)
        ratio=(lp-behavior).clamp(-20,20).exp()
        value=-torch.minimum(ratio*advantage,ratio.clamp(1-cfg['rl_clip'],1+cfg['rl_clip'])*advantage)
        return value.sum(),lp
    for i in range(0,len(y),chunk):
        value,lp=checkpoint(head,h[i:i+chunk],y[i:i+chunk],old[i:i+chunk],use_reentrant=False)
        losses.append(value);replayed.extend(lp.detach().tolist())
    replay=torch.tensor(replayed);delta=replay-old;ratios=delta.exp()
    stats={'mean_abs_logp_mismatch':float(delta.abs().mean()),'max_abs_logp_mismatch':float(delta.abs().max()),
        'mean_ratio':float(ratios.mean()),'ratio_min':float(ratios.min()),'ratio_max':float(ratios.max()),
        'ratio_clipped_fraction':float(((ratios<1-cfg['rl_clip'])|(ratios>1+cfg['rl_clip'])).float().mean()),
        'replay_logp':replayed}
    return torch.stack(losses).sum()/len(y),stats


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--resume',action='store_true');args=ap.parse_args()
    verify_stage('policy');cfg=read('config.json');torch.set_num_threads(4);torch.manual_seed(cfg['seed']+1000)
    assert not (H/'checkpoints/policy_final/manifest.json').exists(),'Policy already finished'
    rolling=Path('/dev/shm/liquid-native028/rolling_policy.pt')
    assert args.resume or not rolling.exists(),'Inspect partial policy state first'
    model,tok,meta,before,descriptors,native,factors,baseline,masters,wrapper=load_trainable()
    assert before==read('reports/preflight.json')['all699_parent_hashes']
    state,_=load_parts(H/'checkpoints/sft_final')
    with torch.no_grad():
        for k,p in factors.items():p.copy_(state['factors'][k])
        for k,p in native.items():p.copy_(state['native'][k])
        for k,p in masters.items():p.copy_(state['masters'][k])
    del state;gc.collect();opt=make_optimizer(factors,masters,policy=True)
    rows=read('data/train_code.json')[:8];anchors=read('data/anchors.json')
    cache=torch.load(H/'data/parent_anchor_top32.pt.bin',weights_only=True)
    updates=done=0;groups=[]
    if args.resume:
        state=torch.load(rolling,weights_only=True)
        with torch.no_grad():
            for k,p in factors.items():p.copy_(state['factors'][k])
            for k,p in native.items():p.copy_(state['native'][k])
            for k,p in masters.items():p.copy_(state['masters'][k])
        opt.load_state_dict(state['optimizer']);torch.set_rng_state(state['rng'])
        updates=state['step'];done=state['extra']['done'];groups=state['extra']['groups'];del state
    started=time.monotonic()
    for index,row in enumerate(rows):
        if index<done:continue
        group_path=f'rollouts/group{index:02d}.json'
        if (H/group_path).exists():
            group=read(group_path);assert group['id']==row['id'] and group['preceding_updates']==updates
        else:
            group={'id':row['id'],'index':index,'preceding_updates':updates,'samples':[],'answers_or_cases_in_prompt':False}
        if len(group['samples'])<cfg['rl_group_samples']:
            for j in range(len(group['samples']),cfg['rl_group_samples']):
                gen=torch.Generator().manual_seed(cfg['seed']+10000+index*10+j)
                sample_result=sample(model,tok,row,gen);sample_result['seed']=cfg['seed']+10000+index*10+j
                group['samples'].append(sample_result);save(group_path,group)
                print('POLICY028_SAMPLE',index,j,sample_result['reward'],sample_result['passed'],sample_result['tokens'],flush=True)
            save(group_path,group)
        assert len(group['samples'])==4
        rewards=torch.tensor([r['reward'] for r in group['samples']]);sd=float(rewards.std(unbiased=False))
        replay_stats=[];losses=[];kl=None;norm=None;counts={};events=[]
        if sd>1e-8:
            adv=(rewards-rewards.mean())/sd;clear_grad(opt,native)
            for item,a in zip(group['samples'],adv.tolist()):
                value,stats=replay_loss(model,item,a);losses.append(float(value.detach()));(value/4).backward()
                replay_stats.append(stats);del value
            ids,gold,_=encode(tok,anchors[index],False);value=anchor_loss(model,ids,gold,cache[anchors[index]['id']])
            kl=float(value.detach());(cfg['rl_retention_weight']*value).backward();del value,ids,gold
            norm,counts,events=update(model,opt,native,factors,baseline,masters);updates+=1
        else:adv=torch.zeros(4)
        result={'index':index,'id':row['id'],'rewards':rewards.tolist(),'advantages':adv.tolist(),
            'reward_std':sd,'updated':sd>1e-8,'policy_updates':updates,'replay_stats':replay_stats,
            'policy_losses':losses,'anchor_coarse_KL':kl,'gradient_norm':norm,**counts,'projection_events':len(events),
            'no_fake_update_on_zero_variance':True,**memory()}
        groups.append(result);done=index+1
        state=payload(model,native,factors,masters,opt,'policy_working',updates,{'done':done,'groups':groups})
        temp=rolling.with_suffix('.tmp');torch.save(state,temp);temp.replace(rolling);del state
        save('reports/policy_groups.json',groups)
        status=read('status.json');status.update(status='training_policy_main',policy_updates=updates,policy_groups_completed=done,optimizer_updates=96+updates);save('status.json',status)
        print('POLICY028_GROUP',index,'updated',sd>1e-8,flush=True);gc.collect()
    export(model,native,factors,baseline,masters,opt,before,descriptors,'policy_final',updates,{'sft_steps':96,'policy_groups':groups})
    save('reports/policy_training.json',{'status':'complete_pending_quality','groups':8,'samples':32,'updates':updates,
        'skipped_zero_variance':sum(not g['updated'] for g in groups),'all_groups':groups,
        'scope':'bounded group-relative PPO prototype; not full DAPO/GRPO or larger-teacher OPD',
        'seconds_descriptive_only':time.monotonic()-started,**memory()})
    clear_grad(opt,native);wrapper.close();print('POLICY028_COMPLETE',updates,flush=True)
if __name__=='__main__':main()
