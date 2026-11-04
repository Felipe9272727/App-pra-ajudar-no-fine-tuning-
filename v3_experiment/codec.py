"""Learned linear byte autoencoder + official NCM multiscale residual VQ.

Experimental short-answer codec, NOT the authors' neural Transformer VQ-VAE.
Encoder: PCA. Codebooks: k-means. Decoder: closed-form ridge. No gradients.
"""
from types import SimpleNamespace
import torch
from torch import nn
import torch.nn.functional as F
from vendor.ncm.quant import MultiscaleResidualVectorQuantizer

LEVELS=[1,2,4,8]
SIZES=[16,32,64,256]
WIDTH=8
STOP=256
DIM=64


def bytes_tensor(text):
    data=list(text.encode('utf-8'))
    if len(data)>WIDTH:raise ValueError('Answer outside preregistered 8-byte scope')
    return torch.tensor(data+[STOP]*(WIDTH-len(data)),dtype=torch.long)


class ByteConceptCodec(nn.Module):
    def __init__(self):
        super().__init__()
        self.mean=nn.Parameter(torch.zeros(257),requires_grad=False)
        self.basis=nn.Parameter(torch.zeros(257,DIM),requires_grad=False)
        self.decoder=nn.Parameter(torch.zeros(DIM+1,257),requires_grad=False)
        self.vq=MultiscaleResidualVectorQuantizer(SIZES,DIM,
            SimpleNamespace(use_manual_levels=True,manual_levels=LEVELS),
            quant_resi={'enabled':False},pre_quant_norm_type='none')
        self.requires_grad_(False).eval()

    def continuous(self,ids):return (F.one_hot(ids,257).float()-self.mean)@self.basis

    def logits(self,z):return torch.cat([z,torch.ones(*z.shape[:-1],1)],-1)@self.decoder

    def text(self,z):
        ids=self.logits(z).argmax(-1).tolist()
        if STOP in ids:ids=ids[:ids.index(STOP)]
        return bytes(ids).decode('utf-8',errors='replace')

    def nearest(self,z,level):
        c=self.vq.embeddings[level].weight
        return self.vq._distances(z.reshape(-1,DIM),c).argmin(-1).view(z.shape[:-1])

    def pooled(self,z,size):return F.interpolate(z.transpose(1,2),size=size,mode='area').transpose(1,2)

    def update(self,z,indices,level):
        return self.vq.get_next_autoregressive_input(level,z,self.vq.embeddings[level](indices))[0]

    @torch.inference_mode()
    def fit(self,train_answers):
        gen=torch.Generator().manual_seed(180431)
        alphabet=torch.tensor(list(b'0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        ids=alphabet[torch.randint(len(alphabet),(4096,WIDTH),generator=gen)]
        general=torch.randint(0,256,ids.shape,generator=gen)
        choose=torch.rand(ids.shape,generator=gen)<.08
        ids[choose]=general[choose]
        lengths=torch.randint(1,WIDTH,(len(ids),1),generator=gen)
        ids[torch.arange(WIDTH).view(1,-1)>=lengths]=STOP
        examples=torch.stack([bytes_tensor(a) for a in train_answers])
        ids=torch.cat([ids,examples.repeat(8,1)])
        counts=torch.bincount(ids.flatten(),minlength=257).float()
        mean=counts/counts.sum();cov=torch.diag(mean)-mean[:,None]*mean[None,:]
        _,vectors=torch.linalg.eigh(cov)
        self.mean.copy_(mean);self.basis.copy_(vectors[:,-DIM:].flip(1))
        target=self.continuous(ids);residual=target.clone();z=torch.zeros_like(target)
        fit=[]
        for i,size in enumerate(LEVELS):
            pooled=self.pooled(residual,size).reshape(-1,DIM)
            if len(pooled)>12000:pooled=pooled[torch.randperm(len(pooled),generator=gen)[:12000]]
            torch.manual_seed(880+i)
            self.vq.kmeans_init_level(i,pooled,n_iters=12)
            indices=self.nearest(self.pooled(residual,size),i)
            old=z.clone();z=self.update(z,indices,i);residual=target-z
            fit.append({'level':i,'positions':size,'codes':SIZES[i],
                'mean_squared_error':float(residual.square().mean()),
                'nonzero_code_values':int(self.vq.embeddings[i].weight.count_nonzero())})
            print('CODEC_LEVEL',fit[-1],flush=True)
        flat=z.reshape(-1,DIM)
        x=torch.cat([flat,torch.ones(len(flat),1)],1)
        y=F.one_hot(ids.flatten(),257).float()
        reg=1e-3*torch.eye(DIM+1);reg[-1,-1]=1e-8
        self.decoder.copy_(torch.linalg.solve(x.T@x+reg,x.T@y))
        codes=self.vq.z_to_idx(self.continuous(examples))
        reconstructed=self.vq.idx_to_zhats(codes,return_zlevels=False)[0][-1]
        outputs=self.logits(reconstructed).argmax(-1)
        valid=torch.arange(WIDTH)[None,:]<=torch.tensor([min(len(a.encode()),WIDTH-1) for a in train_answers])[:,None]
        report={'method':'PCA encoder, official NCM RVQ with k-means, ridge byte decoder',
            'synthetic_codec_sequences':4096,'answer_sequence_repetitions':8,
            'train_byte_accuracy':float((outputs[valid]==examples[valid]).float().mean()),
            'train_exact_reconstruction':float((outputs==examples).all(-1).float().mean()),
            'levels':fit,'backward_passes':0,'uses_heldout':False}
        assert report['train_byte_accuracy']>=.95,report
        return report


def load_codec(path):
    saved=torch.load(path,weights_only=True);codec=ByteConceptCodec()
    codec.load_state_dict(saved['state']);return codec
