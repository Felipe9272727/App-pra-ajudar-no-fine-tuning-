"""One preregistered supervised closed-form rewrite; no optimizer/backward."""
import json,time
from core import *

@torch.inference_mode()
def collect(model,tok,row):
    ids=e.cr.prompt(tok,row['prompt']);ans=tok.encode(row['solution']+tok.eos_token,add_special_tokens=False)
    joined=torch.cat([ids,torch.tensor([ans])],dim=1);acts={}
    def xhook(module,args):acts['x']=args[0][0,-len(ans):].detach().float().clone()
    def zhook(module,args):acts['h']=args[0][0,-len(ans):].detach().float().clone()
    h1=model.model.language_model.layers[31].mlp.down_proj.register_forward_pre_hook(xhook)
    h2=model.model.language_model.norm.register_forward_pre_hook(zhook)
    try:out=model(input_ids=joined[:,:-1],use_cache=False,logits_to_keep=len(ans))
    finally:h1.remove();h2.remove()
    logits=out.logits[0].float();gold=torch.tensor(ans);top=logits.topk(8,-1).indices
    d=targets(acts['h'],gold,top,model.get_output_embeddings().weight,
              1+model.model.language_model.norm.weight.float())
    return {'x':acts['x'],'h':acts['h'],'delta':d,'gold':gold,'top':top,
           'meta':{'id':row['id'],'tokens':len(ans),'wrong_next_tokens':int((top[:,0]!=gold).sum()),
                   'mean_nll':float(torch.nn.functional.cross_entropy(logits,gold)),
                   'token_accuracy':float((top[:,0]==gold).float().mean()),
                   'max_hidden_change_fraction':float((d.norm(dim=-1)/acts['h'].norm(dim=-1)).max())}}

@torch.inference_mode()
def main():
    frozen()
    if (HERE/'checkpoints/candidate.pt').exists():
        finish_diagnostics();return
    m,t,meta=load_variant('parent');before={n:tensor_hash(p) for n,p in m.named_parameters()}
    parent=weight(m).detach().clone();parent_path=HERE/'checkpoints/parent_matrix.pt'
    if parent_path.exists():assert tensor_hash(torch.load(parent_path,weights_only=True)['dense_weight'])==tensor_hash(parent)
    else:tensor_checkpoint({'dense_weight':parent,'parameter':PARAM},parent_path)
    rows=json.loads((HERE/'taught.json').read_text());states=[]
    for row in rows:
        dest=HERE/'states'/('human_'+row['id'].split('/')[-1]+'.pt')
        if dest.exists():s=torch.load(dest,weights_only=True)
        else:
            s=collect(m,t,row);s['data_sha256']=sha(HERE/'taught.json');tensor_checkpoint(s,dest)
        assert s['data_sha256']==sha(HERE/'taught.json');states.append(s)
        print('GOLD',json.dumps(s['meta']),flush=True)
    protect=HERE/'states/language.pt'
    if protect.exists():xp=torch.load(protect,weights_only=True)['x']
    else:
        xs=[]
        for text in e.DATA['anchors']:
            ids=t(text,return_tensors='pt',add_special_tokens=False)['input_ids']
            def hook(module,args):xs.append(args[0][0,-min(8,ids.shape[1]):].detach().float().clone())
            h=m.model.language_model.layers[31].mlp.down_proj.register_forward_pre_hook(hook)
            try:m(input_ids=ids,use_cache=False,logits_to_keep=1)
            finally:h.remove()
        xp=torch.cat(xs);tensor_checkpoint({'x':xp},protect)
    x=torch.cat([s['x'] for s in states]+[xp]).double()
    d=torch.cat([s['delta'] for s in states]+[torch.zeros(len(xp),1024)]).double()
    scale=x.norm(dim=-1,keepdim=True).clamp_min(1e-12);x=x/scale;d=d/scale
    gram=x@x.T;lam=1e-4*float(gram.diagonal().mean())
    coeff=torch.linalg.solve(gram+lam*torch.eye(len(x),dtype=torch.float64),d)
    change=(coeff.T@x).float();norm_ratio=float(change.norm()/parent.float().norm())
    applied_scale=min(1.,.20/max(norm_ratio,1e-12));change*=applied_scale
    written=(parent.float()+change).to(parent.dtype);weight(m).copy_(written)
    changed=[n for n,p in m.named_parameters() if tensor_hash(p)!=before[n]];assert changed==[PARAM],changed
    patch={'parameter':PARAM,'dense_weight':written.cpu(),'parent_sha256':PARENT_HASH,
           'parent_tensor_sha256':tensor_hash(parent),'written_tensor_sha256':tensor_hash(written),
           'data_sha256':sha(HERE/'taught.json'),'method':'RMSNorm sphere-margin targets; dual ridge; existing last down_proj'}
    tensor_checkpoint(patch,HERE/'checkpoints/candidate.pt')
    audit={'parent_sha256':PARENT_HASH,'candidate_sha256':sha(HERE/'checkpoints/candidate.pt'),
        'changed_tensors':changed,'changed_bf16_values':int((parent.view(torch.int16)!=written.view(torch.int16)).sum()),
        'parent_tensors_checked':len(before),'supervised_tokens':sum(s['meta']['tokens'] for s in states),'language_protection_positions':len(xp),
        'ridge_lambda':lam,'unclipped_relative_frobenius':norm_ratio,'applied_scale':applied_scale,
        'actual_relative_frobenius':float((written.float()-parent.float()).norm()/parent.float().norm()),
        'backward_passes':0}
    save('construction.json',audit)
    finish_diagnostics(m,t)

@torch.inference_mode()
def finish_diagnostics(model=None,tok=None):
    if (HERE/'teaching.json').exists():
        assert json.loads((HERE/'teaching.json').read_text())['candidate_sha256']==sha(HERE/'checkpoints/candidate.pt')
        print('TEACHING_COMPLETE_SKIP',flush=True);return
    audit=json.loads((HERE/'construction.json').read_text());assert audit['candidate_sha256']==sha(HERE/'checkpoints/candidate.pt')
    if model is None:model,tok,_=load_variant('edited')
    diagnostic=json.loads((HERE/'diagnostics_progress.json').read_text()) if (HERE/'diagnostics_progress.json').exists() else []
    for row in json.loads((HERE/'taught.json').read_text()):
        if row['id'] in {r['id'] for r in diagnostic}:continue
        old=torch.load(HERE/'states'/('human_'+row['id'].split('/')[-1]+'.pt'),weights_only=True)
        new=collect(model,tok,row)['meta'];diagnostic.append({'id':row['id'],'before':old['meta'],'after':new})
        save('diagnostics_progress.json',diagnostic);print('AFTER_TEACH',json.dumps(new),flush=True)
    audit.update(diagnostics=diagnostic,cache_probe=e.cr.cache_check(model,tok,2),architecture=e.cr.check_architecture(model,2))
    save('teaching.json',audit);print('SAVED_CANDIDATE',audit['candidate_sha256'],flush=True)

if __name__=='__main__':main()
