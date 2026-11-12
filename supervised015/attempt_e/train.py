"""Repair only native termination labels; continue the remaining original readout budget."""
import sys,json,io,gc,time,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE.parent))
from supervised015.attempt_d import train as d
from train_runtime import torch,e,materialize,tensor_hash,PARENT_HASH
import checkpoint
HERE=ROOT/'supervised015/attempt_e';D=HERE.parent/'attempt_d';C=HERE.parent/'attempt_c'
def save(name,value):e.cr.atomic_json(HERE/name,value)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_archive(directory):
    m=json.loads((directory/'manifest.json').read_text());assert m['format']=='torch-zip-parts-v1';buffer=io.BytesIO();whole=hashlib.sha256()
    for p in m['parts']:
        b=(directory/p['path']).read_bytes();assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'];whole.update(b);buffer.write(b)
    assert buffer.tell()==m['bytes'] and whole.hexdigest()==m['stream_sha256'];buffer.seek(0);return torch.load(buffer,weights_only=True)

def main():
    for p,h in json.loads((HERE/'frozen.json').read_text()).items():assert sha(ROOT/p)==h,p
    assert not (HERE/'steps.jsonl').exists() and not (HERE/'checkpoints/candidate/manifest.json').exists()
    cfg=json.loads((HERE/'config.json').read_text());start=time.monotonic();model,tok,parent,meta=d.load_c()
    assert model.generation_config.eos_token_id==cfg['native_terminal_id']
    before={n:tensor_hash(p) for n,p in model.named_parameters()};materialize(model)
    norm=model.model.language_model.norm;embedding=model.lm_head.weight.detach();old=dict(model.named_parameters())[d.NAME].detach().clone();original=parent['dense_weight'].detach().clone()
    old_changed=int((old.view(torch.int16)!=original.view(torch.int16)).count_nonzero())
    state=read_archive(D/'checkpoints/training_state');data=read_archive(D/'training_cache');dm=json.loads((D/'checkpoints/candidate/manifest.json').read_text())
    assert tensor_hash(state['master'].to(torch.bfloat16))==dm['tensor_sha256']
    mapping=[];offset=0
    for row in data['rows']:
        index=offset+row['tokens']-1;assert int(data['gold'][index])==cfg['old_terminal_id'];data['gold'][index]=cfg['native_terminal_id']
        mapping.append({'id':row['id'],'global_token_index':index,'old_label':cfg['old_terminal_id'],'new_label':cfg['native_terminal_id'],'program_tokens_unchanged':True});offset+=row['tokens']
    assert offset==len(data['gold'])==1098;save('terminal_label_repair.json',{'mapping':mapping,'source_cache_manifest_sha256':sha(D/'training_cache/manifest.json'),'runtime_generation_eos_unchanged':True,'reference_programs_and_official_tests_unchanged':True})
    master=torch.nn.Parameter(state['master'].detach().clone(),requires_grad=True);del model,parent;gc.collect();torch.set_grad_enabled(True)
    optimizer=torch.optim.AdamW([master],lr=cfg['learning_rate'],betas=(.9,.999),eps=1e-8,weight_decay=0.);optimizer.load_state_dict(state['optimizer']);del state
    baseline=old.float();budget=cfg['max_relative_frobenius']*float(baseline.norm());priority=next(i for i,r in enumerate(data['rows']) if r['id']==cfg['priority_task']);weights=torch.where(data['groups']==priority,cfg['priority_weight'],1.)
    margins,competitors,preds,h=d.scan(master,norm,embedding,data,cfg['chunk_tokens']);save('initial_corrected_diagnostics.json',{'correct_tokens':int((preds==data['gold']).sum()),'minimum_margin':float(margins.min()),'labels_corrected':len(mapping)})
    history=[]
    for step in range(1,cfg['max_optimizer_steps']+1):
        if bool((margins>=cfg['minimum_margin']).all()):break
        optimizer.zero_grad(set_to_none=True);losses=[]
        for offset in range(0,len(margins),cfg['chunk_tokens']):
            end=offset+cfg['chunk_tokens'];x=data['x'][offset:end];r=data['r'][offset:end];y=data['gold'][offset:end];c=competitors[offset:end]
            hh=norm(r+torch.nn.functional.linear(x,master.to(torch.bfloat16)));selected=torch.stack([embedding[y],embedding[c]],1);pair=torch.bmm(selected,hh.unsqueeze(-1)).squeeze(-1);surrogate=(pair[:,0]-pair[:,1]).float()
            real=surrogate-surrogate.detach()+margins[offset:end];losses.append((torch.relu(cfg['minimum_margin']-real).square()*weights[offset:end]).sum())
        loss=torch.stack(losses).sum()/weights.sum();number=float(loss.detach());loss.backward();assert bool(torch.isfinite(master.grad).all());optimizer.step()
        with torch.no_grad():
            delta=master-baseline;length=float(delta.norm())
            if length>budget:master.copy_(baseline+delta*(budget/length))
        margins,competitors,preds,h=d.scan(master,norm,embedding,data,cfg['chunk_tokens'])
        entry={'continuation_step':step,'total_readout_steps':6+step,'loss_before_update':number,'correct_tokens':int((preds==data['gold']).sum()),'total_tokens':1098,'minimum_real_dense_margin':float(margins.min()),'relative_frobenius':float((master-baseline).norm()/baseline.norm())};history.append(entry)
        with (HERE/'steps.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
        save('learning_curve.json',history);print('UPDATE',json.dumps(entry),flush=True);del losses,loss;gc.collect()
    final=master.detach().to(torch.bfloat16).contiguous();assert bool(torch.isfinite(final).all())
    d.archive(HERE/'checkpoints/training_state',{'master':master.detach(),'optimizer':optimizer.state_dict(),'torch_rng_state':torch.get_rng_state(),'source_D_master':dm['stream_sha256']})
    writer=checkpoint.PartsWriter(HERE/'checkpoints/candidate');writer.write(final.view(torch.uint8).numpy().tobytes());writer.close();changed=int((final.view(torch.int16)!=old.view(torch.int16)).count_nonzero());new_changed=int((final.view(torch.int16)!=original.view(torch.int16)).count_nonzero());ct=json.loads((C/'training_complete.json').read_text())
    m={'format':'raw-bf16-readout-parts-v1','parent_specialist_stream_sha256':d.CH,'original_parent_sha256':PARENT_HASH,'training_state_initialized_from_D_patch':dm['stream_sha256'],'tensor_name':d.NAME,'shape':list(final.shape),'dtype':str(final.dtype),'bytes':final.numel()*final.element_size(),
       'parts':writer.parts,'stream_sha256':writer.hash.hexdigest(),'parent_tensor_sha256':tensor_hash(old),'tensor_sha256':tensor_hash(final),'changed_values_vs_c':changed,'changed_values_vs_original_parent':ct['changed_values_vs_original_parent']-old_changed+new_changed,'changed_tensors_vs_original_parent':ct['changed_tensors_vs_original_parent']-int(old_changed>0)+int(new_changed>0)}
    save('checkpoints/candidate/manifest.json',m);correct=int((preds==data['gold']).sum());del optimizer,master,embedding,norm,data,h,baseline;gc.collect();torch.set_grad_enabled(False)
    model,_,_,_=d.load_c()
    with torch.inference_mode():dict(model.named_parameters())[d.NAME].copy_(final)
    after={n:tensor_hash(p) for n,p in model.named_parameters()};assert all(after[n]==v for n,v in before.items() if n!=d.NAME) and after[d.NAME]==m['tensor_sha256']
    report={'status':'training_complete','eligible_additional_tensors':1,'eligible_additional_parameters':final.numel(),'matrix_updates_in_continuation':len(history),'matrix_updates_in_D_and_E':6+len(history),'new_total_gradient_updates_in_lineage':44+len(history),
      'changed_values_vs_c':changed,'changed_tensors_vs_original_parent':m['changed_tensors_vs_original_parent'],'changed_values_vs_original_parent':m['changed_values_vs_original_parent'],'checkpoint_stream_sha256':m['stream_sha256'],'parent_specialist_stream_sha256':d.CH,
      'all_other_698_parameter_tensors_bitwise_unchanged':True,'vision_tensors_unchanged':153,'corrected_cached_training_tokens':1098,'final_cached_correct_tokens':correct,'minimum_cached_margin':float(margins.min()),'terminal_labels_repaired':8,'native_generation_configuration_changed':False,'seconds':time.monotonic()-start,'architecture':e.cr.check_architecture(model,2)}
    report['architecture'].update(backward_passes=report['new_total_gradient_updates_in_lineage'],limitations='Trained hybrid; terminal-label repair and taught fit are not general intelligence.')
    save('training_complete.json',report);print('CHECKPOINT_COMPLETE',json.dumps({k:v for k,v in report.items() if k!='architecture'}),flush=True)
if __name__=='__main__':main()
