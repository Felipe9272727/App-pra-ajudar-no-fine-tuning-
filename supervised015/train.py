"""Full-parameter specialist SFT, explicitly authorized by the user."""
import gc,json,random,time
from train_runtime import *
from optimizer import BackwardAdafactor
import checkpoint as exact_checkpoint

def memory():
    s=Path('/proc/self/status').read_text();return {'rss_kb':int(s.split('VmRSS:')[1].split()[0]),'peak_rss_kb':int(s.split('VmHWM:')[1].split()[0])}
def verify_frozen():
    for path,h in json.loads((HERE/'frozen.json').read_text()).items():assert sha(ROOT/path)==h,path

@torch.no_grad()
def measure(model,tok,rows):
    model.eval();out=[]
    for row in rows:
        ids,gold=encode(tok,row);hidden=model.model(input_ids=ids,use_cache=False).last_hidden_state[0,-len(gold):]
        nll=0.;correct=0;minimum=float('inf')
        for start in range(0,len(gold),16):
            y=gold[start:start+16];logits=model.lm_head(hidden[start:start+16]).float()
            nll+=float(torch.nn.functional.cross_entropy(logits,y,reduction='sum'));correct+=int((logits.argmax(-1)==y).sum())
            chosen=logits.gather(1,y[:,None]).squeeze(1);logits.scatter_(1,y[:,None],float('-inf'))
            minimum=min(minimum,float((chosen-logits.max(-1).values).min()))
        out.append({'id':row['id'],'tokens':len(gold),'nll':nll/len(gold),'correct_tokens':correct,'minimum_gold_margin':minimum})
    model.train();model.model.visual.eval();return out

def main():
    verify_frozen();config=json.loads((HERE/'config.json').read_text())
    assert not (HERE/'checkpoints/final/manifest.json').exists(),'Existing completed specialist must not be overwritten'
    assert not (HERE/'steps.jsonl').exists(),'Prior training log exists: inspect state before restarting'
    torch.manual_seed(config['seed'])
    model,tok,meta,eligible,wrapper=load_trainable()
    parent_hashes={n:tensor_hash(p) for n,p in model.named_parameters()}
    rows=json.loads((HERE/'train.json').read_text());start=time.monotonic()
    initial=measure(model,tok,rows);save('initial_teacher_forcing.json',initial)
    opt=BackwardAdafactor(eligible,lr=config['learning_rate']);ever=set();steps=0;history=[];rng=random.Random(config['seed'])
    for epoch in range(1,config['max_epochs']+1):
        order=list(range(len(rows)));rng.shuffle(order)
        for offset in range(0,len(order),config['batch_examples']):
            indices=order[offset:offset+config['batch_examples']];opt.reset();losses=[]
            for index in indices:
                ids,gold=encode(tok,rows[index]);losses.append(loss(model,ids,gold))
            value=torch.stack(losses).mean();number=float(value.detach());value.backward()
            assert set(opt.calls)==set(eligible) and set(opt.calls.values())=={1}
            project_gains(model);steps+=1;ever.update(n for n,s in opt.stats.items() if s['nonzero'])
            entry={'epoch':epoch,'optimizer_step':steps,'ids':[rows[i]['id'] for i in indices],
                 'loss_before_update':number,'nonzero_gradient_tensors':sum(s['nonzero'] for s in opt.stats.values()),**memory()}
            with (HERE/'steps.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
            save('status.json',{'status':'supervised_full_text_training','model_process_active':True,
                'optimizer_steps_completed':steps,'epoch':epoch,'backward_passes':steps,'eligible_text_tensors':len(eligible),
                'ever_nonzero_gradient_tensors':len(ever),'parent_sha256':PARENT_HASH,'checkpoint_promoted':False,
                'process_continues_in_background':False,'updated_unix':time.time()})
            print('TRAIN',json.dumps(entry),flush=True)
            del losses,value;gc.collect()
        measured=measure(model,tok,rows);history.append({'epoch':epoch,'optimizer_steps':steps,'rows':measured});save('learning_curve.json',history)
        tokens=sum(r['tokens'] for r in measured);correct=sum(r['correct_tokens'] for r in measured);margin=min(r['minimum_gold_margin'] for r in measured)
        print('EPOCH',epoch,'correct',correct,'tokens',tokens,'minimum_margin',margin,flush=True)
        if correct==tokens and margin>=config['stop_minimum_margin']:break
    opt.close();wrapper.close();model.eval();model.requires_grad_(False);torch.set_grad_enabled(False)
    torch.save({'optimizers':opt.state_dict(),'optimizer_steps':steps,'python_rng_state':rng.getstate(),'torch_rng_state':torch.get_rng_state()},HERE/'checkpoints/optimizer.pt')
    del opt;gc.collect()
    # A second immutable parent is loaded only after all gradients are released.
    parent,_,_,_=load();manifest=exact_checkpoint.write(HERE/'checkpoints/final',model,parent,PARENT_HASH)
    exact_checkpoint.restore(HERE/'checkpoints/final',parent,PARENT_HASH)
    assert all(tensor_hash(dict(parent.named_parameters())[n])==spec['tensor_sha256'] for n,spec in manifest['tensors'].items())
    after={n:tensor_hash(p) for n,p in model.named_parameters()}
    assert all(after[n]==h for n,h in parent_hashes.items() if not text_parameter(n)),'Vision weights changed'
    audit={'status':'training_complete','eligible_tensors':len(eligible),'eligible_parameters':sum(p.numel() for p in eligible.values()),
       'optimizer_steps':steps,'backward_passes':steps,'epochs':history[-1]['epoch'],'ever_nonzero_gradient_tensors':sorted(ever),
       'changed_text_tensors':manifest['changed_tensors'],'changed_scalar_values':manifest['changed_values'],
       'checkpoint_compressed_bytes':manifest['compressed_bytes'],'checkpoint_stream_sha256':manifest['stream_sha256'],
       'vision_tensors_unchanged':sum(not text_parameter(n) for n in after),'seconds':time.monotonic()-start,
       'checkpoint_restore_verified_all_text_tensors':True,
       'initial_teacher_forcing':initial,'final_teacher_forcing':history[-1]['rows'],'memory':memory(),
       'architecture':e.cr.check_architecture(model,2),'parent_sha256':PARENT_HASH}
    save('training_complete.json',audit);print('CHECKPOINT_COMPLETE',manifest['compressed_bytes'],manifest['changed_tensors'],flush=True)

if __name__=='__main__':main()
