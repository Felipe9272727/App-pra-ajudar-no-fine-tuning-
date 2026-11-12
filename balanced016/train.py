"""Bounded balanced joint Loop/mHC/Liquid-temporal calibration from exact015E."""
import sys,json,gc,math,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'balanced016';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
from train_runtime import torch,e,materialize,CheckpointVisits,loss,project_gains,tensor_hash
from optimizer import BackwardAdafactor
import checkpoint
from supervised015.attempt_e.restore import load_d as load_e
E_HASH='33f4d2b0fa0d36329ec0bd59d94ca9054c5c4ab549b7a551743a955711679b85'
def save(name,value):e.cr.atomic_json(HERE/name,value)
def sha(path):return tr.sha(path)
def verify_frozen():
    for path,h in json.loads((HERE/'frozen.json').read_text()).items():assert sha(ROOT/path)==h,path

def encode(tok,row):
    prompt=e.cr.prompt(tok,row['prompt']);answer=tok.encode(row['solution'],add_special_tokens=False)+[248044];ids=torch.cat([prompt,torch.tensor([answer])],1)
    return ids[:,:-1],torch.tensor(answer)

def memory():
    s=Path('/proc/self/status').read_text();return {'rss_kb':int(s.split('VmRSS:')[1].split()[0]),'peak_rss_kb':int(s.split('VmHWM:')[1].split()[0])}

def family(name):
    if '.mhc_' in name:return 'mhc_routing'
    if 'native_visit_gain' in name:return 'loop_visit_gain'
    if any(s in name for s in ['.linear_attn.in_proj_a.','.linear_attn.in_proj_b.','.linear_attn.A_log','.linear_attn.dt_bias','.linear_attn.conv1d.']):return 'liquid_temporal'
    if 'layernorm' in name or '.norm.' in name:return 'normalization'
    return 'last_mlp_projection'

@torch.no_grad()
def measure(model,tok,rows):
    model.eval();result=[]
    for row in rows:
        ids,gold=encode(tok,row);h=model.model(input_ids=ids,use_cache=False).last_hidden_state[0,-len(gold):];total=0.;correct=0
        for offset in range(0,len(gold),16):
            y=gold[offset:offset+16];logits=model.lm_head(h[offset:offset+16]).float();total+=float(torch.nn.functional.cross_entropy(logits,y,reduction='sum'));correct+=int((logits.argmax(-1)==y).sum())
        result.append({'id':row['id'],'tokens':len(gold),'nll':total/len(gold),'correct_tokens':correct})
    model.train();model.model.visual.eval();return result

@torch.no_grad()
def trust_project(eligible,baseline,cfg):
    for n,p in eligible.items():
        ref=baseline[n];delta=p.detach().float()-ref;limit=cfg['trust_relative']*max(float(ref.norm()),math.sqrt(p.numel())*cfg['trust_rms_floor']);length=float(delta.norm())
        if length>limit:p.copy_((ref+delta*(limit/length)).to(p.dtype))

def main():
    verify_frozen();assert not (HERE/'steps.jsonl').exists() and not (HERE/'checkpoints/final/manifest.json').exists(),'Inspect previous state; never blindly restart'
    (HERE/'checkpoints').mkdir(exist_ok=True)
    cfg=json.loads((HERE/'config.json').read_text());selection=json.loads((HERE/'trainable.json').read_text());code=json.loads((HERE/'code_retention_train.json').read_text());general=json.loads((HERE/'general_train.json').read_text());torch.manual_seed(cfg['seed']);start=time.monotonic()
    model,tok,meta,em=load_e();assert em['stream_sha256']==E_HASH and model.generation_config.eos_token_id==cfg['native_eos_id'];materialize(model)
    before={n:tensor_hash(p) for n,p in model.named_parameters()};selected=set(selection['names']);torch.set_grad_enabled(True);model.train();model.model.visual.eval()
    for n,p in model.named_parameters():p.requires_grad_(n in selected)
    eligible={n:p for n,p in model.named_parameters() if p.requires_grad};assert set(eligible)==selected and sum(p.numel() for p in eligible.values())==6345904
    baseline={n:p.detach().float().clone() for n,p in eligible.items()};wrapper=CheckpointVisits(model)
    initial=measure(model,tok,code+general);save('initial_teacher_forcing.json',initial)
    # Same real graph and selected leaf accumulation, but no weight update.
    smoke=BackwardAdafactor(eligible,update=False);values=[]
    for row in [code[0],general[0]]:
        ids,gold=encode(tok,row);values.append(loss(model,ids,gold))
    value=torch.stack(values).mean();value.backward();assert set(smoke.calls)==selected and set(smoke.calls.values())=={1}
    assert all(wrapper.calls[(i,v)]>0 for i in range(4,28) for v in (0,1)), 'Both loop visits must execute in backward preflight'
    assert all(tensor_hash(dict(model.named_parameters())[n])==h for n,h in before.items())
    save('backward_preflight.json',{'status':'passed_no_weight_change','selected_tensors':len(eligible),'gradient_present':len(smoke.calls),'nonzero_gradient_tensors':sum(s['nonzero'] for s in smoke.stats.values()),'loss':float(value.detach()),'all_699_parameter_hashes_unchanged':True,'family_nonzero':{f:sum(s['nonzero'] for n,s in smoke.stats.items() if family(n)==f) for f in sorted({family(n) for n in eligible})},**memory()})
    smoke.close();del smoke,values,value;gc.collect();opt=BackwardAdafactor(eligible,lr=cfg['learning_rate']);ever=set()
    for step in range(1,cfg['optimizer_steps']+1):
        examples=[code[(step-1)%len(code)],general[(step-1)%len(general)]];opt.reset();values=[]
        for row in examples:
            ids,gold=encode(tok,row);values.append(loss(model,ids,gold))
        value=cfg['code_example_weight']*values[0]+cfg['general_example_weight']*values[1];number=float(value.detach());value.backward();assert set(opt.calls)==selected and set(opt.calls.values())=={1}
        trust_project(eligible,baseline,cfg);project_gains(model);ever.update(n for n,s in opt.stats.items() if s['nonzero'])
        entry={'step':step,'examples':[r['id'] for r in examples],'loss_before_update':number,'code_loss':float(values[0].detach()),'general_loss':float(values[1].detach()),'nonzero_gradient_tensors':sum(s['nonzero'] for s in opt.stats.values()),'nonzero_by_family':{f:sum(s['nonzero'] for n,s in opt.stats.items() if family(n)==f) for f in sorted({family(n) for n in eligible})},**memory()}
        with (HERE/'steps.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
        save('status.json',{'status':'balanced_joint_training','model_process_active':True,'optimizer_steps_completed':step,'selected_tensors':len(eligible),'parent_specialist_stream':E_HASH,'checkpoint_promoted':False,'process_continues_in_background':False});print('TRAIN',json.dumps(entry),flush=True)
        del values,value;gc.collect()
    final=measure(model,tok,code+general);save('final_teacher_forcing.json',final);opt.close();wrapper.close();model.eval();model.requires_grad_(False);torch.set_grad_enabled(False)
    torch.save({'optimizers':opt.state_dict(),'optimizer_steps':cfg['optimizer_steps'],'torch_rng_state':torch.get_rng_state()},HERE/'checkpoints/optimizer.pt');del opt,baseline;gc.collect()
    after={n:tensor_hash(p) for n,p in model.named_parameters()};assert all(after[n]==h for n,h in before.items() if n not in selected),'Frozen parameter changed'
    parent,_,_,_=load_e();m=checkpoint.write(HERE/'checkpoints/final',model,parent,E_HASH);checkpoint.restore(HERE/'checkpoints/final',parent,E_HASH)
    assert all(tensor_hash(dict(parent.named_parameters())[n])==spec['tensor_sha256'] for n,spec in m['tensors'].items())
    assert all(bool(torch.isfinite(p).all()) for p in model.parameters())
    audit={'status':'training_complete','eligible_tensors':len(eligible),'eligible_parameters':selection['parameter_count'],'ever_nonzero_gradient_tensors':sorted(ever),'optimizer_steps':cfg['optimizer_steps'],'changed_text_tensors':m['changed_tensors'],'changed_values_vs_E':m['changed_values'],'checkpoint_compressed_bytes':m['compressed_bytes'],'checkpoint_stream_sha256':m['stream_sha256'],'parent_specialist_stream_sha256':E_HASH,
      'frozen_parameter_tensors_unchanged':sum(n not in selected for n in before),'vision_tensors_unchanged':153,'cold_restore_verified_all_546_text_hashes':True,'all_699_parameter_tensors_finite':True,'training_programs_general':len(general),'code_retention_programs':len(code),'initial_teacher_forcing':initial,'final_teacher_forcing':final,'architecture':e.cr.check_architecture(model,2),'seconds':time.monotonic()-start,**memory()}
    audit['architecture'].update(backward_passes=16,limitations='Jointly calibrated Qwen-sized Loop/mHC and Liquid-inspired operators; fit is not evidence of general improvement.')
    save('training_complete.json',audit);save('status.json',{'status':'training_complete_pending_screen','model_process_active':False,'checkpoint_promoted':False,'process_continues_in_background':False});print('CHECKPOINT_COMPLETE',m['compressed_bytes'],m['changed_tensors'],flush=True)
if __name__=='__main__':main()
