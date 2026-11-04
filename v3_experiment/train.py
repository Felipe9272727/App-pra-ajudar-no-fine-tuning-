"""Resumable closed-form learning of the V3 experimental NCM hierarchy."""
import argparse
import gc
import json
from pathlib import Path
import torch
import torch.nn.functional as F
from runtime import *
from codec import bytes_tensor


def save_torch(path,data):
    temporary=path.with_suffix(path.suffix+'.tmp')
    torch.save(data,temporary);temporary.replace(path)


@torch.inference_mode()
def fit_codec():
    if (HERE/'codec.pt').exists():print('CODEC_ALREADY_SAVED',flush=True);return
    status(status='training_codec',experiment=True,backward_passes=0)
    codec=ByteConceptCodec()
    report=codec.fit([r['answer'] for r in DATA['train']])
    save_torch(HERE/'codec.pt',{'state':codec.state_dict(),'data_sha256':DATA_HASH,
                'scope':'linear byte autoencoder + official NCM RVQ'})
    atomic_json(HERE/'codec_fit.json',report)
    status(status='codec_checkpointed',codec_sha256=file_hash(HERE/'codec.pt'))
    print('CODEC_FIT',report,flush=True)


@torch.inference_mode()
def collect():
    folder=HERE/'features';folder.mkdir(exist_ok=True)
    finished=len(list(folder.glob('train_*.pt')))
    if finished==len(DATA['train']):print('FEATURES_ALREADY_COMPLETE',flush=True);return
    status(status='collecting_hybrid_features',model_process_active=True)
    model,write=parent_model();tok=tokenizer();codec=load_codec(HERE/'codec.pt')
    embeds=byte_embeddings(model,tok)
    save_torch(HERE/'query_embeddings.pt',{'bytes':embeds,'parent_patch_sha256':file_hash(PARENT_PATCH)})
    exp=NCMExperiment(model,tok,codec,embeds)
    for j,row in enumerate(DATA['train']):
        output=folder/f'train_{j:03d}.pt'
        if output.exists():continue
        gen=torch.Generator().manual_seed(320011+j)
        prefix,context,_=exp.prefix(row['question'])
        truth=codec.continuous(bytes_tensor(row['answer'])[None])
        z=torch.zeros_like(truth);features=[];targets=[]
        for i,size in enumerate(LEVELS):
            x=exp.features(prefix,context,z,i)[0]
            residual=codec.pooled(truth-z,size)
            indices=codec.nearest(residual,i)
            target=codec.vq.embeddings[i](indices)[0]
            features.append(x.to(torch.float16));targets.append(target.clone())
            # Train robustness to imperfect earlier concepts, as a fixed rule.
            used=indices.clone()
            noise=torch.rand(used.shape,generator=gen)<.1
            random_codes=torch.randint(SIZES[i],used.shape,generator=gen)
            used[noise]=random_codes[noise]
            z=codec.update(z,used,i)
        save_torch(output,{'id':row['id'],'x':features,'y':targets,'data_sha256':DATA_HASH,
                    'seed_for_this_stream':320011+j})
        status(status='collecting_hybrid_features',train_examples_completed=j+1,
               parent_weight_write=write,architecture=architecture_check(model))
        if (j+1)%4==0:print('FEATURES',j+1,len(DATA['train']),flush=True)
    status(status='features_checkpointed',model_process_active=False)


@torch.inference_mode()
def fit_heads():
    files=sorted((HERE/'features').glob('train_*.pt'))
    assert len(files)==len(DATA['train'])
    records=[torch.load(p,weights_only=True) for p in files]
    assert all(r['data_sha256']==DATA_HASH for r in records)
    all_heads={str(lam):[] for lam in DATA['protocol']['ridge_candidates']};stats=[]
    for i,size in enumerate(LEVELS):
        x=torch.cat([r['x'][i] for r in records]).float()
        y=torch.cat([r['y'][i] for r in records]).float()
        mean=x.mean(0);scale=x.std(0).clamp_min(.05)
        x=(x-mean)/scale;x=x/x.norm(dim=-1,keepdim=True).clamp_min(1e-6)
        target_mean=y.mean(0);centered=y-target_mean
        gram=x@x.T
        for lam in DATA['protocol']['ridge_candidates']:
            estimate=torch.linalg.solve(gram+lam*torch.eye(len(x)),centered)
            weight=(x.T@estimate).to(torch.float16)
            predicted=x@weight.float()+target_mean
            all_heads[str(lam)].append({'mean':mean,'scale':scale,'weight':weight,
                'target_mean':target_mean})
            stats.append({'level':i,'positions':size,'ridge':lam,'feature_rows':len(x),
                'learned_weights':weight.numel(),'nonzero_weights':int(weight.count_nonzero()),
                'train_residual_mse':float((predicted-y).square().mean())})
    archive=[]
    for n,lam in enumerate(DATA['protocol']['ridge_candidates']):
        key=f'head_{n:02d}';path=HERE/f'{key}.pt'
        save_torch(path,{'heads':all_heads[str(lam)],'ridge':lam,'data_sha256':DATA_HASH,
            'codec_sha256':file_hash(HERE/'codec.pt'),'parent_patch_sha256':file_hash(PARENT_PATCH),
            'scope':'EXPERIMENTO: NCM-inspired short answers with active SenseNova and Liquid'})
        archive.append({'id':key,'ridge':lam,'checkpoint':str(path.relative_to(ROOT)),
            'sha256':file_hash(path),'status':'awaiting_development'})
    atomic_json(HERE/'head_fit.json',{'backward_passes':0,'method':'closed-form ridge on frozen hybrid features',
        'conditioning_corruption_probability':.1,'rows':stats,'training_examples':len(records)})
    atomic_json(HERE/'archive.json',{'data_sha256':DATA_HASH,'heads':archive})
    status(status='heads_checkpointed',model_process_active=False)
    print('HEADS_SAVED',archive,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['codec','collect','fit'])
    a=p.parse_args();{'codec':fit_codec,'collect':collect,'fit':fit_heads}[a.phase]()
