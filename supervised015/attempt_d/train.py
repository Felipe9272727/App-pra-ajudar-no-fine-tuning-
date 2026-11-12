"""Bounded supervised native-cache readout refinement; forced replay is TRAINING ONLY."""
import sys,json,hashlib,gc,io,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE.parent))
import train_runtime as tr
from train_runtime import torch,e,load,PARENT_HASH,tensor_hash,materialize
import checkpoint
from transformers import LogitsProcessor,LogitsProcessorList
HERE=ROOT/'supervised015/attempt_d';B=HERE.parent/'attempt_b';C=HERE.parent/'attempt_c'
BH='c2f851b064b9656e356fe2c37985df88d598bf2fd358903d1a06fcf53b659ca7';CH='05687b52a1efb934cec6d5f7ce4c63b62969dd88cec1c2f85364c0afac1cbb15'
NAME='model.language_model.layers.31.mlp.down_proj.weight'
def save(name,value):e.cr.atomic_json(HERE/name,value)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
@torch.inference_mode()
def load_c():
    model,tok,parent,meta=load();b=checkpoint.restore(B/'checkpoints/final',model,PARENT_HASH);assert b['stream_sha256']==BH
    c=checkpoint.restore(C/'checkpoints/final',model,BH);assert c['stream_sha256']==CH
    return model,tok,parent,meta

def archive(directory,value):
    directory=Path(directory);assert not (directory/'manifest.json').exists()
    buffer=io.BytesIO();torch.save(value,buffer);writer=checkpoint.PartsWriter(directory);writer.write(buffer.getbuffer());writer.close()
    m={'format':'torch-zip-parts-v1','parts':writer.parts,'bytes':len(buffer.getbuffer()),'stream_sha256':writer.hash.hexdigest()};(directory/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');return m

@torch.inference_mode()
def collect(model,tok,rows):
    allx=[];allr=[];allh=[];ally=[];groups=[];latest={};handles=[];raw=[]
    layer=model.model.language_model.layers[31]
    def xhook(module,args):latest['x']=args[0][0,-1].detach().clone()
    def rhook(module,args):latest['r']=args[0][0,-1].detach().clone()
    def hhook(module,args,out):latest['h']=out[0,-1].detach().clone()
    handles=[layer.mlp.down_proj.register_forward_pre_hook(xhook),layer.post_attention_layernorm.register_forward_pre_hook(rhook),model.model.language_model.norm.register_forward_hook(hhook)]
    try:
        for group,row in enumerate(rows):
            prompt=e.cr.prompt(tok,row['prompt']);gold=tok.encode(row['solution']+tok.eos_token,add_special_tokens=False);seen=[];record=[]
            class TeacherTrainingOnly(LogitsProcessor):
                def __call__(self,input_ids,scores):
                    i=input_ids.shape[1]-prompt.shape[1];target=gold[i];values,indices=scores[0].topk(2);other=values[1] if int(indices[0])==target else values[0]
                    seen.append((latest['x'],latest['r'],latest['h']));record.append({'index':i,'gold_id':target,'raw_argmax':int(indices[0]),'raw_gold_margin':float(scores[0,target]-other)})
                    out=torch.full_like(scores,float('-inf'));out[0,target]=0.;return out
            torch.manual_seed(0)
            out=model.generate(input_ids=prompt,max_new_tokens=len(gold),use_cache=True,do_sample=False,pad_token_id=tok.eos_token_id,logits_processor=LogitsProcessorList([TeacherTrainingOnly()]))[0,prompt.shape[1]:]
            assert out.tolist()==gold and len(seen)==len(gold),'Incomplete forced training replay; never score this replay'
            allx.extend(a for a,_,_ in seen);allr.extend(b for _,b,_ in seen);allh.extend(c for _,_,c in seen);ally.extend(gold);groups.extend([group]*len(gold))
            raw.append({'id':row['id'],'tokens':len(gold),'raw_correct_tokens':sum(r['gold_id']==r['raw_argmax'] for r in record),'raw_first_divergence':next((r for r in record if r['gold_id']!=r['raw_argmax']),None),'decisions':record,'forced_training_replay_not_scored':True})
            save('collection_progress.json',raw);print('COLLECT',row['id'],len(gold),raw[-1]['raw_correct_tokens'],flush=True)
    finally:
        for h in handles:h.remove()
    return {'x':torch.stack(allx),'r':torch.stack(allr),'h_native':torch.stack(allh),'gold':torch.tensor(ally),'groups':torch.tensor(groups),'rows':raw}

@torch.no_grad()
def scan(master,norm,embedding,data,chunk):
    margins=[];competitors=[];preds=[];hidden=[]
    w=master.to(torch.bfloat16)
    for start in range(0,len(data['gold']),chunk):
        h=norm(data['r'][start:start+chunk]+torch.nn.functional.linear(data['x'][start:start+chunk],w));logits=torch.nn.functional.linear(h,embedding).float();y=data['gold'][start:start+chunk]
        preds.append(logits.argmax(-1));gold=logits.gather(1,y[:,None]).squeeze(1);logits.scatter_(1,y[:,None],float('-inf'));v,c=logits.max(-1);margins.append(gold-v);competitors.append(c);hidden.append(h)
    return torch.cat(margins),torch.cat(competitors),torch.cat(preds),torch.cat(hidden)

def main():
    for p,h in json.loads((HERE/'frozen.json').read_text()).items():assert sha(ROOT/p)==h,p
    assert not (HERE/'steps.jsonl').exists() and not (HERE/'checkpoints/candidate/manifest.json').exists(),'Inspect existing D before restart'
    cfg=json.loads((HERE/'config.json').read_text());rows=json.loads((C/'train.json').read_text());torch.manual_seed(cfg['seed']);start=time.monotonic()
    model,tok,parent,meta=load_c();before={n:tensor_hash(p) for n,p in model.named_parameters()};collected=collect(model,tok,rows)
    # Inference tensors must be cloned outside InferenceMode for readout backward.
    materialize(model)
    data={k:(v.detach().clone() if torch.is_tensor(v) else v) for k,v in collected.items()};del collected;gc.collect()
    norm=model.model.language_model.norm;embedding=model.lm_head.weight.detach();old=dict(model.named_parameters())[NAME].detach().clone();original=parent['dense_weight'].detach().clone()
    old_changed=int((old.view(torch.int16)!=original.view(torch.int16)).count_nonzero());master=torch.nn.Parameter(old.float(),requires_grad=True)
    del model,parent;gc.collect();torch.set_grad_enabled(True)
    archive(HERE/'training_cache',data)
    margins,competitors,preds,h=scan(master,norm,embedding,data,cfg['chunk_tokens']);preflight={'tokens':len(margins),'raw_native_correct':sum(r['raw_correct_tokens'] for r in data['rows']),
       'reconstructed_correct':int((preds==data['gold']).sum()),'raw_reconstructed_argmax_agreement':sum(int(p)==r['raw_argmax'] for p,r in zip(preds,[d for r in data['rows'] for d in r['decisions']]))/len(preds),
       'native_hidden_max_abs_rounding_difference':float((h-data['h_native']).abs().max()),'minimum_margin':float(margins.min()),'forced_replay_not_benchmark_score':True}
    assert preflight['raw_reconstructed_argmax_agreement']>=.99,preflight
    assert preflight['native_hidden_max_abs_rounding_difference']<=.0625,preflight
    save('preflight.json',preflight);print('PREFLIGHT',json.dumps(preflight),flush=True)
    optimizer=torch.optim.AdamW([master],lr=cfg['learning_rate'],betas=(.9,.999),eps=1e-8,weight_decay=0.)
    baseline=old.float();budget=cfg['max_relative_frobenius']*float(baseline.norm());priority=next(i for i,r in enumerate(rows) if r['id']==cfg['priority_task']);weights=torch.where(data['groups']==priority,cfg['priority_weight'],1.)
    history=[]
    for step in range(1,cfg['max_optimizer_steps']+1):
        if bool((margins>=cfg['minimum_margin']).all()):break
        optimizer.zero_grad(set_to_none=True);losses=[]
        for offset in range(0,len(margins),cfg['chunk_tokens']):
            end=offset+cfg['chunk_tokens'];x=data['x'][offset:end];r=data['r'][offset:end];y=data['gold'][offset:end];c=competitors[offset:end]
            hh=norm(r+torch.nn.functional.linear(x,master.to(torch.bfloat16)))
            selected=torch.stack([embedding[y],embedding[c]],dim=1)
            pair=torch.bmm(selected,hh.unsqueeze(-1)).squeeze(-1);surrogate=(pair[:,0]-pair[:,1]).float()
            real_margin=surrogate-surrogate.detach()+margins[offset:end]
            losses.append((torch.relu(cfg['minimum_margin']-real_margin).square()*weights[offset:end]).sum())
        loss=torch.stack(losses).sum()/weights.sum();number=float(loss.detach());loss.backward();assert bool(torch.isfinite(master.grad).all());optimizer.step()
        with torch.no_grad():
            delta=master-baseline;length=float(delta.norm())
            if length>budget:master.copy_(baseline+delta*(budget/length))
        margins,competitors,preds,h=scan(master,norm,embedding,data,cfg['chunk_tokens'])
        entry={'step':step,'supervised_margin_loss_before_update':number,'correct_tokens':int((preds==data['gold']).sum()),'total_tokens':len(margins),'minimum_real_dense_margin':float(margins.min()),'relative_frobenius':float((master-baseline).norm()/baseline.norm())}
        history.append(entry)
        with (HERE/'steps.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
        save('learning_curve.json',history);print('UPDATE',json.dumps(entry),flush=True);del losses,loss;gc.collect()
    final=master.detach().to(torch.bfloat16).contiguous();assert bool(torch.isfinite(final).all())
    optimizer_manifest=archive(HERE/'checkpoints/training_state',{'master':master.detach(),'optimizer':optimizer.state_dict(),'torch_rng_state':torch.get_rng_state()})
    writer=checkpoint.PartsWriter(HERE/'checkpoints/candidate');writer.write(final.view(torch.uint8).numpy().tobytes());writer.close()
    changed=int((final.view(torch.int16)!=old.view(torch.int16)).count_nonzero());new_changed=int((final.view(torch.int16)!=original.view(torch.int16)).count_nonzero());ct=json.loads((C/'training_complete.json').read_text())
    manifest={'format':'raw-bf16-readout-parts-v1','parent_specialist_stream_sha256':CH,'original_parent_sha256':PARENT_HASH,'tensor_name':NAME,'shape':list(final.shape),'dtype':str(final.dtype),'bytes':final.numel()*final.element_size(),
       'parts':writer.parts,'stream_sha256':writer.hash.hexdigest(),'parent_tensor_sha256':tensor_hash(old),'tensor_sha256':tensor_hash(final),'changed_values_vs_c':changed,
       'changed_values_vs_original_parent':ct['changed_values_vs_original_parent']-old_changed+new_changed,'changed_tensors_vs_original_parent':ct['changed_tensors_vs_original_parent']-int(old_changed>0)+int(new_changed>0)}
    save('checkpoints/candidate/manifest.json',manifest)
    del optimizer,master,embedding,norm,data,h,baseline;gc.collect();torch.set_grad_enabled(False)
    model,_,_,_=load_c();target=dict(model.named_parameters())[NAME]
    with torch.inference_mode():target.copy_(final)
    after={n:tensor_hash(p) for n,p in model.named_parameters()};assert all(after[n]==v for n,v in before.items() if n!=NAME);assert after[NAME]==manifest['tensor_sha256']
    report={'status':'training_complete','eligible_additional_tensors':1,'eligible_additional_parameters':final.numel(),'matrix_updates':len(history),'original_full_text_training_steps':38,'new_total_gradient_updates_in_lineage':38+len(history),
       'changed_tensors_vs_c':int(changed>0),'changed_values_vs_c':changed,'changed_tensors_vs_original_parent':manifest['changed_tensors_vs_original_parent'],'changed_values_vs_original_parent':manifest['changed_values_vs_original_parent'],
       'checkpoint_stream_sha256':manifest['stream_sha256'],'parent_specialist_stream_sha256':CH,'all_other_698_parameter_tensors_bitwise_unchanged':True,'vision_tensors_unchanged':153,'cached_training_tokens':preflight['tokens'],
       'final_cached_correct_tokens':int((preds==torch.tensor([d['gold_id'] for row in json.loads((HERE/'collection_progress.json').read_text()) for d in row['decisions']])).sum()),'minimum_cached_margin':float(margins.min()),'seconds':time.monotonic()-start,
       'architecture':e.cr.check_architecture(model,2),'preflight':preflight,'forced_training_replay_was_not_scored':True}
    report['architecture'].update(backward_passes=report['new_total_gradient_updates_in_lineage'],limitations='Qwen-sized trained hybrid; cached training fit does not establish general reasoning or superiority.')
    save('training_complete.json',report);print('CHECKPOINT_COMPLETE',json.dumps({k:v for k,v in report.items() if k!='architecture'}),flush=True)
if __name__=='__main__':main()
