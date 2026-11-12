"""Bounded full-text critical-token SFT from the exact preserved B checkpoint."""
import sys,gc,json,time,hashlib,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];B=HERE.parent/'attempt_b'
sys.path.insert(0,str(HERE.parent))
import train_runtime as tr
from train_runtime import *
from optimizer import BackwardAdafactor
import checkpoint
HERE=ROOT/'supervised015/attempt_c';tr.HERE=HERE
B=HERE.parent/'attempt_b';B_HASH='c2f851b064b9656e356fe2c37985df88d598bf2fd358903d1a06fcf53b659ca7'

def load_b():
    model,tok,parent,meta=load();m=checkpoint.restore(B/'checkpoints/final',model,PARENT_HASH);assert m['stream_sha256']==B_HASH
    return model,tok,meta

def memory():
    s=Path('/proc/self/status').read_text();return {'rss_kb':int(s.split('VmRSS:')[1].split()[0]),'peak_rss_kb':int(s.split('VmHWM:')[1].split()[0])}

@torch.no_grad()
def measure(model,tok,rows):
    model.eval();result=[]
    for row in rows:
        ids,gold=encode(tok,row);hidden=model.model(input_ids=ids,use_cache=False).last_hidden_state[0,-len(gold):]
        nll=0.;correct=0;minimum=float('inf');first=None;weakest=None
        for start in range(0,len(gold),16):
            y=gold[start:start+16];logits=model.lm_head(hidden[start:start+16]).float();pred=logits.argmax(-1)
            nll+=float(torch.nn.functional.cross_entropy(logits,y,reduction='sum'));correct+=int((pred==y).sum())
            values=logits.gather(1,y[:,None]).squeeze(1);logits.scatter_(1,y[:,None],float('-inf'));margins=values-logits.max(-1).values
            for j in range(len(y)):
                detail={'token_index':start+j,'gold_id':int(y[j]),'predicted_id':int(pred[j]),'margin':float(margins[j]),
                        'gold_piece':tok.decode([int(y[j])]),'predicted_piece':tok.decode([int(pred[j])])}
                if int(pred[j])!=int(y[j]) and first is None:first=detail
                if detail['margin']<minimum:minimum=detail['margin'];weakest=detail
        result.append({'id':row['id'],'tokens':len(gold),'nll':nll/len(gold),'correct_tokens':correct,'minimum_gold_margin':minimum,
                       'first_wrong':first,'selected_token':first if first is not None else weakest})
    model.train();model.model.visual.eval();return result

def token_loss(model,tok,row,selection):
    ids,gold=encode(tok,row);index=selection['token_index'];cut=ids.shape[1]-len(gold)+index+1
    prefix=ids[:,:cut];h=model.model(input_ids=prefix,use_cache=False).last_hidden_state[0,-1:]
    logits=model.lm_head(h).float();target=gold[index:index+1]
    number=int(target[0]);value=logits[0,number].detach();alternative=logits[0].detach().clone();alternative[number]=float('-inf')
    diagnostic={'prefix_tokens':cut,'gold_token_index':index,'truncated_prefix_gold_margin_before_update':float(value-alternative.max()),'truncated_prefix_argmax_before_update':int(logits.argmax(-1)[0])}
    return torch.nn.functional.cross_entropy(logits,target),diagnostic

@torch.no_grad()
def cumulative_changes(model):
    original,_,_,_=load();base=dict(original.named_parameters());changed=0;tensors=0
    for name,p in model.named_parameters():
        if not text_parameter(name):assert tensor_hash(p)==tensor_hash(base[name]);continue
        kind=torch.int16 if p.element_size()==2 else torch.int32;a=p.detach().view(kind).flatten();b=base[name].detach().view(kind).flatten()
        count=sum(int((x!=y).count_nonzero()) for x,y in zip(a.split(1024*1024),b.split(1024*1024)))
        changed+=count;tensors+=count>0
    del original;gc.collect();return {'changed_tensors_vs_original_parent':tensors,'changed_values_vs_original_parent':changed}

def main():
    for path,h in json.loads((HERE/'frozen.json').read_text()).items():assert sha(ROOT/path)==h,path
    assert not (HERE/'steps.jsonl').exists() and not (HERE/'checkpoints/final/manifest.json').exists(),'Inspect existing trial before restart'
    cfg=json.loads((HERE/'config.json').read_text());rows=json.loads((B/'train.json').read_text());bank={r['id']:r for r in rows};torch.manual_seed(cfg['seed']);started=time.monotonic()
    model,tok,meta=load_b();materialize(model);eligible=enable_training(model);wrapper=CheckpointVisits(model)
    vision={n:tensor_hash(p) for n,p in model.named_parameters() if not text_parameter(n)}
    opt=BackwardAdafactor(eligible,lr=cfg['learning_rate']);state=torch.load(B/'checkpoints/optimizer.pt',weights_only=True);opt.load_state_dict(state['optimizers']);del state
    for optimizer in opt.optimizers.values():optimizer.param_groups[0]['lr']=cfg['learning_rate']
    history=[];ever=set();steps=0;initial=measure(model,tok,rows);save('initial_teacher_forcing.json',initial);measured=initial
    for step in range(1,cfg['max_optimizer_steps']+1):
        if all(r['correct_tokens']==r['tokens'] for r in measured) and min(r['minimum_gold_margin'] for r in measured)>=cfg['stop_minimum_margin']:break
        priority=cfg['priority_failed_targets']
        ranking=sorted(measured,key=lambda r:(0 if r['first_wrong'] and r['id'] in priority else 1 if r['first_wrong'] else 2,r['selected_token']['margin'],r['id']))
        chosen=ranking[:2];opt.reset();losses=[];diagnostics=[]
        for row in chosen:
            value,diag=token_loss(model,tok,bank[row['id']],row['selected_token']);losses.append(value);diagnostics.append({'id':row['id'],**row['selected_token'],**diag})
        value=torch.stack(losses).mean();number=float(value.detach());value.backward();assert set(opt.calls)==set(eligible) and set(opt.calls.values())=={1}
        project_gains(model);steps+=1;ever.update(n for n,s in opt.stats.items() if s['nonzero'])
        entry={'optimizer_step_added':steps,'total_optimizer_steps':32+steps,'loss_before_update':number,'mined_training_tokens':diagnostics,'nonzero_gradient_tensors':sum(s['nonzero'] for s in opt.stats.values()),**memory()}
        with (HERE/'steps.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
        print('UPDATE',json.dumps(entry),flush=True);del losses,value;gc.collect();measured=measure(model,tok,rows)
        history.append({'optimizer_steps_added':steps,'rows':measured});save('learning_curve.json',history)
        save('status.json',{'status':'critical_token_full_text_training','model_process_active':True,'optimizer_steps_added':steps,'parent_specialist_stream':B_HASH,'checkpoint_promoted':False,'process_continues_in_background':False})
        print('MEASURE',steps,'correct',sum(r['correct_tokens'] for r in measured),'of1098',flush=True)
    opt.close();wrapper.close();model.eval();model.requires_grad_(False);torch.set_grad_enabled(False)
    torch.save({'optimizers':opt.state_dict(),'optimizer_steps':32+steps,'torch_rng_state':torch.get_rng_state()},HERE/'checkpoints/optimizer.pt');del opt;gc.collect()
    parent,_,_=load_b();manifest=checkpoint.write(HERE/'checkpoints/final',model,parent,B_HASH);checkpoint.restore(HERE/'checkpoints/final',parent,B_HASH)
    assert all(tensor_hash(dict(parent.named_parameters())[n])==s['tensor_sha256'] for n,s in manifest['tensors'].items());del parent;gc.collect()
    assert all(tensor_hash(dict(model.named_parameters())[n])==h for n,h in vision.items())
    overall=cumulative_changes(model)
    report={'status':'training_complete','eligible_tensors':len(eligible),'eligible_parameters':sum(p.numel() for p in eligible.values()),'optimizer_steps_added':steps,'optimizer_steps':32+steps,'backward_passes':32+steps,'ever_nonzero_gradient_tensors':sorted(ever),
      'changed_text_tensors_vs_b':manifest['changed_tensors'],'changed_values_vs_b':manifest['changed_values'],**overall,'checkpoint_compressed_bytes':manifest['compressed_bytes'],'checkpoint_stream_sha256':manifest['stream_sha256'],
      'checkpoint_restore_verified_all_text_tensors':True,'vision_tensors_unchanged':len(vision),'initial_teacher_forcing':initial,'final_teacher_forcing':measured,'seconds':time.monotonic()-started,'memory':memory(),
      'original_parent_sha256':PARENT_HASH,'parent_specialist_stream_sha256':B_HASH,'architecture':e.cr.check_architecture(model,2)}
    report['architecture']['backward_passes']=32+steps;report['architecture']['limitations']='Qwen-sized Loop/mHC and Liquid-inspired operators; trained parameters do not imply reasoning superiority.'
    save('training_complete.json',report);print('CHECKPOINT_COMPLETE',manifest['compressed_bytes'],manifest['changed_tensors'],flush=True)
if __name__=='__main__':main()
