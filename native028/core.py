"""Conservative low-rank + native-controller learning on the preserved main model."""
import collections, gc, hashlib, json, math, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
from train_runtime import torch, tensor_hash, materialize, CheckpointVisits
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint
from spec026.io_parts import save_json, save_parts, load_parts, file_hash
H=ROOT/'native028'


def tensor_hash(value):
    # Same bytes as the legacy audit, without allocating a whole-embedding
    # Python bytes copy (~509MB). Buffer hashing is read-only.
    array=value.detach().cpu().contiguous().view(torch.uint8).numpy()
    return hashlib.sha256(memoryview(array)).hexdigest()


def read(name): return json.loads((H/name).read_text())
def save(name,value): save_json(H/name,value)
def memory():
    s=Path('/proc/self/status').read_text()
    return {k:int(s.split(label+':')[1].split()[0]) for k,label in [('rss_kb','VmRSS'),('peak_rss_kb','VmHWM')]}
def verify_source(path,expected):
    actual=file_hash(ROOT/path)
    if actual==expected:return True
    revisions=read('recovery/source_revision.json')['files']
    record=revisions.get(path,{})
    return record.get('before_sha256')==expected and record.get('after_sha256')==actual

def verify_frozen():
    assert all(verify_source(p,h) for p,h in read('frozen.json').items()),'Frozen source/data mismatch'
def base_parameters(model): return {n:p for n,p in model.named_parameters() if '.lora_' not in n}
def controls():
    old=json.loads((ROOT/'loop025/trainable.json').read_text())
    names=set(old['names'])-set(old['exit_names'])
    assert len(names)==276
    return names


def encode(tok,row,thinking=False):
    messages=row.get('messages',[{'role':'user','content':row['prompt']}]) if 'messages' not in row else row['messages']
    kwargs={'tools':row['schemas']} if 'schemas' in row else {}
    prefix=tok.apply_chat_template(messages,add_generation_prompt=True,enable_thinking=thinking,
        tokenize=True,return_dict=False,**kwargs)
    answer=(row['plan']+'\n</think>\n\n' if thinking else '')+row['solution']
    gold=tok.encode(answer,add_special_tokens=False)+[248044]
    seq=torch.tensor([prefix+gold],dtype=torch.long)
    assert len(prefix)+len(gold)<=768,(row['id'],len(prefix),len(gold))
    return seq[:,:-1],torch.tensor(gold,dtype=torch.long),len(prefix)


class LowRankLinear(nn.Linear):
    def forward(self,x):
        base=F.linear(x,self.weight,self.bias)
        a=self.lora_A.to(dtype=x.dtype);b=self.lora_B.to(dtype=x.dtype)
        return base+F.linear(F.linear(x,a),b)


def install(model,rank=8):
    names=controls();descriptors=[]
    for name,module in list(model.named_modules()):
        if not name.startswith('model.language_model.layers.') or not isinstance(module,nn.Linear):continue
        physical=int(name.split('.')[3])
        if not 4<=physical<28 or name+'.weight' in names:continue
        n=module.weight.shape[1];r=min(rank,n)
        j=torch.arange(n,dtype=torch.float64)+.5;k=torch.arange(r,dtype=torch.float64)[:,None]
        a=torch.cos(math.pi*k*j/n)*math.sqrt(2/n);a[0]/=math.sqrt(2)
        module.__class__=LowRankLinear
        module.lora_A=nn.Parameter(a.float());module.lora_B=nn.Parameter(torch.zeros(module.weight.shape[0],r))
        module._lora_reference_denom=max(float(module.weight.double().norm()),math.sqrt(module.weight.numel())*read('config.json')['trust_rms_floor'])
        descriptors.append({'module':name,'physical':physical,'shape':list(module.weight.shape),'rank':r})
    for n,p in model.named_parameters():p.requires_grad_('.lora_' in n or n in names)
    assert descriptors
    return descriptors


def load_trainable():
    model,tok,parent,meta=tr.load();del parent
    materialize(model);before={n:tensor_hash(p) for n,p in model.named_parameters()};assert len(before)==699
    model.requires_grad_(False);descriptors=install(model,read('config.json')['rank'])
    native={n:p for n,p in model.named_parameters() if n in controls()}
    factors={n:p for n,p in model.named_parameters() if '.lora_' in n}
    baseline={n:p.detach().float().clone() for n,p in native.items()}
    masters={n:nn.Parameter(v.clone()) for n,v in baseline.items()}
    model.train();model.model.visual.eval();torch.set_grad_enabled(True)
    wrapper=CheckpointVisits(model)
    return model,tok,meta,before,descriptors,native,factors,baseline,masters,wrapper


def hidden(model,ids,gold):
    return model.model(input_ids=ids,use_cache=False).last_hidden_state[0,-len(gold):]
def sft_loss(model,ids,gold):
    h=hidden(model,ids,gold);parts=[];chunk=read('config.json')['head_chunk_tokens']
    def ce(x,y):return F.cross_entropy(F.linear(x,model.get_output_embeddings().weight).float(),y,reduction='sum')
    for i in range(0,len(gold),chunk):parts.append(checkpoint(ce,h[i:i+chunk],gold[i:i+chunk],use_reentrant=False))
    return torch.stack(parts).sum()/len(gold)


def coarse_kl(logits,indices,teacher_logp,teacher_other):
    logits=logits.float();logq=logits.gather(1,indices)-torch.logsumexp(logits,dim=-1,keepdim=True)
    qsum=logq.exp().sum(-1).clamp(max=1-1e-7)
    rest=torch.log1p(-qsum);p=teacher_logp.exp();other=teacher_other.clamp_min(1e-8)
    kl=(p*(teacher_logp-logq)).sum(-1)+other*(other.log()-rest)
    return kl.clamp_min(0)


def anchor_loss(model,ids,gold,cache):
    h=hidden(model,ids,gold);parts=[];chunk=read('config.json')['head_chunk_tokens']
    def kl(x,idx,lp,other):
        return coarse_kl(F.linear(x,model.get_output_embeddings().weight),idx,lp,other).sum()
    for i in range(0,len(gold),chunk):
        parts.append(checkpoint(kl,h[i:i+chunk],cache['indices'][i:i+chunk],cache['logp'][i:i+chunk],cache['other'][i:i+chunk],use_reentrant=False))
    return torch.stack(parts).sum()/len(gold)


def make_optimizer(factors,masters,policy=False):
    cfg=read('config.json')
    return torch.optim.AdamW([{'params':list(factors.values()),'lr':cfg['rl_factor_lr'] if policy else cfg['factor_lr']},
        {'params':list(masters.values()),'lr':cfg['rl_controller_lr'] if policy else cfg['controller_lr']}],betas=(.9,.95),weight_decay=0.,foreach=False)
def clear_grad(opt,native):
    opt.zero_grad(set_to_none=True)
    for p in native.values():p.grad=None


def factor_norm(a,b):
    # ||B A||_F^2 = trace((B^T B)(A A^T)); rank8 Gram matrices avoid
    # materializing every dense projection during each optimizer step.
    aa=a.double();bb=b.double()
    return float(((bb.T@bb)*(aa@aa.T)).sum().clamp_min(0).sqrt())


@torch.no_grad()
def project(model,native,baseline,masters,export=False):
    cfg=read('config.json');events=[]
    for n,p in native.items():
        base=baseline[n];v=masters[n];den=max(float(base.double().norm()),math.sqrt(p.numel())*cfg['trust_rms_floor']);cap=cfg['controller_trust_relative']*den
        if 'native_visit_gain' in n:
            delta=v-base;d=float((delta[1]-delta[0])/2);d=max(-cap/math.sqrt(2),min(cap/math.sqrt(2),d))
            second=max(1e-4,min(1-1e-4,float(base[1])+d));v.copy_(torch.tensor([1-second,second],dtype=v.dtype))
        else:
            delta=v-base;length=float(delta.double().norm())
            if length>cap:v.copy_(base+delta*(cap/length))
        q=v.to(p.dtype);length=float((q.float()-base).double().norm())
        if length>cap+1e-7:
            delta=(v-base).clone();lo=0.;hi=1.
            for _ in range(24):
                mid=(lo+hi)/2;q=(base+delta*mid).to(p.dtype)
                if float((q.float()-base).double().norm())<=cap:lo=mid
                else:hi=mid
            v.copy_(base+delta*lo);q=v.to(p.dtype);events.append({'name':n,'quantized_projection':True})
        p.copy_(q)
        assert float((p.float()-base).double().norm())<=cap+1e-7,n
    for name,m in model.named_modules():
        if not isinstance(m,LowRankLinear):continue
        den=m._lora_reference_denom;cap=cfg['factor_trust_relative']*den
        length=factor_norm(m.lora_A,m.lora_B)
        if length>cap:m.lora_B.mul_(cap/length)
        if export:
            delta=m.lora_B@m.lora_A
            base=m.weight.float();actual=float(((base+delta).to(m.weight.dtype).float()-base).double().norm())
            if actual>cap+1e-7:
                lo=0.;hi=1.;original_b=m.lora_B.detach().clone()
                for _ in range(24):
                    mid=(lo+hi)/2
                    # Evaluate the actual stored-factor operation. FP32 (B*s)@A
                    # can round differently from (B@A)*s at BF16 boundaries.
                    candidate=base+(original_b*mid)@m.lora_A
                    if float((candidate.to(m.weight.dtype).float()-base).double().norm())<=cap:lo=mid
                    else:hi=mid
                m.lora_B.copy_(original_b*lo);events.append({'name':name,'quantized_projection':True})
                assert float(((base+m.lora_B@m.lora_A).to(m.weight.dtype).float()-base).double().norm())<=cap+1e-7
    return events


def update(model,opt,native,factors,baseline,masters):
    assert all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in list(native.values())+list(factors.values())),'Missing/nonfinite gradient'
    for n,p in native.items():masters[n].grad=p.grad.detach().float().clone()
    norm=float(torch.nn.utils.clip_grad_norm_(list(factors.values())+list(masters.values()),read('config.json')['gradient_clip']))
    counts={'factor_nonzero':sum(bool(p.grad.count_nonzero()) for p in factors.values()),'native_nonzero':sum(bool(p.grad.count_nonzero()) for p in native.values())}
    opt.step();events=project(model,native,baseline,masters);clear_grad(opt,native)
    return norm,counts,events


@torch.no_grad()
def folded_hashes(model,before):
    params=base_parameters(model);hashes={n:tensor_hash(p) for n,p in params.items()};changes={}
    for name,m in model.named_modules():
        if not isinstance(m,LowRankLinear):continue
        value=(m.weight.float()+m.lora_B@m.lora_A).to(m.weight.dtype)
        hashes[name+'.weight']=tensor_hash(value)
        changes[name+'.weight']={'changed_values':int((value!=m.weight).count_nonzero()),'relative_l2':float((value.float()-m.weight.float()).double().norm())/m._lora_reference_denom}
    assert set(hashes)==set(before)
    return hashes,changes


def payload(model,native,factors,masters,opt,stage,step,extra=None):
    return {'format':'native028-factors-and-native-controls-v1','parent_sha256':tr.PARENT_HASH,
        'stage':stage,'step':step,'factors':{n:p.detach() for n,p in factors.items()},
        'native':{n:p.detach() for n,p in native.items()},'masters':{n:p.detach() for n,p in masters.items()},
        'optimizer':opt.state_dict(),'rng':torch.get_rng_state(),'extra':extra or {}}


def export(model,native,factors,baseline,masters,opt,before,descriptors,stage,step,extra=None):
    events=project(model,native,baseline,masters,export=True)
    hashes,changes=folded_hashes(model,before);allowed=set(native)|set(changes)
    assert all(hashes[n]==v for n,v in before.items() if n not in allowed)
    data=payload(model,native,factors,masters,opt,stage,step,extra);data['merged_hashes']=hashes
    manifest=save_parts(H/'checkpoints'/stage,data,{'phase':stage,'parent_sha256':tr.PARENT_HASH,'optimizer_RNG_included':True,'steps':step})
    audit={'stage':stage,'step':step,'parent_sha256':tr.PARENT_HASH,'all699_merged_hashes':hashes,
        'changed_native_tensors':sum(hashes[n]!=before[n] for n in native),'changed_native_names':[n for n in native if hashes[n]!=before[n]],
        'changed_folded_projections':sum(v['changed_values']>0 for v in changes.values()),'projection_changes':changes,
        'frozen_base_outside_scope_unchanged':True,'vision153_unchanged':True,'effective_native_parameter_count':sum(p.numel() for p in base_parameters(model).values()),
        'factor_modules':len(descriptors),'factor_values':sum(p.numel() for p in factors.values()),'native_values':sum(p.numel() for p in native.values()),
        'export_projection_events':events,'checkpoint':manifest,**memory()}
    save('reports/'+stage+'.json',audit)
    return manifest


@torch.inference_mode()
def load_variant(variant):
    if variant=='original':
        m,meta=tr.e.cr.load('original');tok=tr.e.cr.tokenizer()
    else:
        m,tok,parent,meta=tr.load();del parent
        if variant!='parent':
            data,manifest=load_parts(H/'checkpoints'/variant);assert data['parent_sha256']==tr.PARENT_HASH
            ps=dict(m.named_parameters())
            for n,v in data['native'].items():ps[n].copy_(v)
            for n,v in data['factors'].items():
                if not n.endswith('.lora_B'):continue
                prefix=n[:-len('.lora_B')];a=data['factors'][prefix+'.lora_A'];w=ps[prefix+'.weight']
                w.copy_((w.float()+v@a).to(w.dtype))
            assert all(tensor_hash(p)==data['merged_hashes'][n] for n,p in m.named_parameters()),'All699 cold hash mismatch'
            meta={**meta,'native028_variant':variant,'checkpoint_sha256':manifest['compressed_sha256'],'all699_hashes_verified':True};del data;gc.collect()
    torch.set_num_threads(4);m.eval();m.requires_grad_(False)
    return m,tok,meta


def grade_general(text,row):
    if '</think>' in text:text=text.rsplit('</think>',1)[1]
    value=text.strip().lower().rstrip('.!?。').strip()
    return value in [str(a).strip().lower() for a in row['answers']]


def delivered(text,thinking):
    if thinking and '</think>' not in text:return ''
    return text.rsplit('</think>',1)[-1].strip()
