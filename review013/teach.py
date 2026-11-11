"""Correct-program teacher forcing -> closed-form local embedding-direction fit.

This is supervised learning by algebra, not SFT/LoRA, a backward pass or an
optimizer. Its surrogate transports an output-token embedding direction to the
loop exit through an identity approximation of the remaining four layers.
That approximation is a hypothesis; only free generation can validate it.
"""
import argparse,json,time
from review_runtime import *

@torch.inference_mode()
def capture():
    verify_frozen();model,tok,_,_=load_variant('parent')
    rows=json.loads((HERE/'train.json').read_text());progress={'rows':[],'parent_sha256':PARENT_HASH}
    states=HERE/'states';states.mkdir(exist_ok=True)
    for row in rows:
        path=states/(row['id']+'.pt')
        if path.exists():
            old=torch.load(path,weights_only=True)
            assert old['row_sha256']==filehash_data(row)
            progress['rows'].append(old['meta']);continue
        prompt=e.cr.prompt(tok,row['prompt']);answer=tok.encode(row['solution']+tok.eos_token,add_special_tokens=False)
        assert len(answer)<160
        ids=torch.cat([prompt,torch.tensor([answer])],dim=1);length=len(answer)
        acts={};vis=[]
        def loop_hook(module,args,out):vis.append(out[0].detach().float().clone())
        def norm_hook(module,args):acts['z']=args[0][0].detach().float().clone()
        h1=model.model.language_model.layers[27].register_forward_hook(loop_hook)
        h2=model.model.language_model.norm.register_forward_pre_hook(norm_hook)
        started=time.monotonic()
        try:
            out=model(input_ids=ids[:,:-1],use_cache=False,logits_to_keep=length)
        finally:h1.remove();h2.remove()
        logits=out.logits[0].float();gold=torch.tensor(answer);pred=logits.argmax(-1)
        nll=torch.nn.functional.cross_entropy(logits,gold,reduction='none')
        f,_=features(vis[0][None],vis[1][None]);f=f[0,-length:]
        # Steering targets from gold-vs-produced embedding directions. No derivative.
        emb=model.get_output_embeddings().weight
        d=emb[gold].float()-emb[pred].float()
        y=.02*d/rms(d);y[gold==pred]=0
        # Fixed uniformly spaced decisions; no candidate/output-dependent selection.
        ix=torch.linspace(0,length-1,min(24,length)).round().long().unique()
        meta={'id':row['id'],'tokens':length,'sampled_decisions':len(ix),
              'teacher_forced_top1':float((pred==gold).float().mean()),'nll':float(nll.mean()),
              'seconds':time.monotonic()-started,'wrong_decisions':int((pred!=gold).sum())}
        tensor_checkpoint({'features':f[ix].cpu(),'target':y[ix].cpu(),
                  'gold':gold[ix],'predicted':pred[ix],'selected_positions':ix,
                  'row_sha256':filehash_data(row),'meta':meta},path)
        progress['rows'].append(meta);save('teaching_progress.json',progress)
        print('TEACH',row['id'],round(meta['nll'],4),len(ix),flush=True)
    progress['status']='complete';progress['total_tokens']=sum(r['tokens'] for r in progress['rows'])
    progress['mean_task_nll']=sum(r['nll'] for r in progress['rows'])/len(rows)
    save('teaching_progress.json',progress)

def filehash_data(row):return hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()

@torch.inference_mode()
def fit():
    verify_frozen();rows=json.loads((HERE/'train.json').read_text())
    states=[torch.load(HERE/'states'/(r['id']+'.pt'),weights_only=True) for r in rows]
    assert all(s['row_sha256']==filehash_data(r) for s,r in zip(states,rows))
    x=torch.cat([s['features'] for s in states]);y=torch.cat([s['target'] for s in states])
    audit={'training_examples':len(rows),'sampled_decisions':len(x),'targets_nonzero':int(y.abs().sum(-1).count_nonzero()),'candidates':{}}
    for kind,dim in [('loop',1024),('joint',2048)]:
        xx=x[:,:dim].double()
        # Deterministic eigendecomposition; no random weight initialization.
        values,vectors=torch.linalg.eigh(xx.T@xx)
        basis=vectors[:,-16:];z=xx@basis;lam=.01*float((z.T@z).diagonal().mean())
        output=torch.linalg.solve(z.T@z+lam*torch.eye(16,dtype=torch.float64),z.T@y.double())
        patch={'kind':kind,'parent_sha256':PARENT_HASH,'cap':.02,'rank':16,
               'input_basis':basis.float(),'output_map':output.float(),
               'training_sha256':filehash(HERE/'train.json'),'method':'PCA16 plus ridge .01 mean Gram diagonal; embedding steering; identity tail approximation'}
        tensor_checkpoint(patch,HERE/'checkpoints'/(kind+'.pt'))
        pred=(xx@basis)@output
        audit['candidates'][kind]={'parameters':basis.numel()+output.numel(),
              'zero_predictor_mse':float(y.square().mean()),'fit_mse':float((pred-y).square().mean()),
              'ridge_lambda':lam,'sha256':filehash(HERE/'checkpoints'/(kind+'.pt'))}
    save('fit.json',audit);print(json.dumps(audit,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['capture','fit']);a=p.parse_args()
    capture() if a.action=='capture' else fit()
