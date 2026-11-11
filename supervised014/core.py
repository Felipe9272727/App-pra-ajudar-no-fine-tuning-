"""Direct update of an EXISTING last-MLP matrix, with an immutable parent."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'supervised014'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,e,torch,PARENT_HASH,tensor_checkpoint
from native010.native_runtime import tensor_hash
PARAM='model.language_model.layers.31.mlp.down_proj.weight'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,obj):e.cr.atomic_json(HERE/n,obj)
def frozen():
    for p,h in json.loads((HERE/'frozen.json').read_text()).items():assert sha(ROOT/p)==h,p
def weight(model):return model.model.language_model.layers[31].mlp.down_proj.weight

@torch.inference_mode()
def rotate_to_margin(h,a,margin=.5):
    """Closest same-norm point satisfying one final-logit halfspace.

    RMSNorm output is g*h/RMS(h). a=(E_gold-E_competitor)*g. On a
    fixed-norm sphere the normalized logit-margin inequality is linear.
    This is geometric projection, with no loss derivative or backward call.
    """
    radius=h.norm(dim=-1,keepdim=True).clamp_min(1e-12)
    anorm=a.norm(dim=-1,keepdim=True).clamp_min(1e-12);v=a/anorm;u=h/radius
    cosine=(u*v).sum(-1,keepdim=True)
    target=(margin/(h.shape[-1]**.5*anorm)).clamp(max=.99)
    perp=u-cosine*v;perp=perp/perp.norm(dim=-1,keepdim=True).clamp_min(1e-12)
    proposed=radius*(target*v+(1-target.square()).sqrt()*perp)
    return torch.where(cosine<target,proposed,h)

@torch.inference_mode()
def targets(h,gold,top,emb,norm_gain):
    wrong=top[:,0]!=gold;result=h.clone()
    ix=wrong.nonzero().flatten()
    if len(ix):
        old=h[ix];new=old.clone();comp=top[ix]
        a=(emb[gold[ix]].float()[:,None]-emb[comp].float())*norm_gain
        for _ in range(8):
            margins=(a*new[:,None]).sum(-1)/(new.square().mean(-1).sqrt().clamp_min(1e-6)[:,None])
            margins[comp==gold[ix,None]]=float('inf')
            choice=margins.argmin(-1);v=a[torch.arange(len(ix)),choice]
            new=rotate_to_margin(new,v,.5)
        delta=new-old
        delta*=torch.clamp(.15*old.norm(dim=-1,keepdim=True)/delta.norm(dim=-1,keepdim=True).clamp_min(1e-12),max=1)
        result[ix]=old+delta
    return result-h

def load_variant(kind):
    if kind=='original':
        m,meta=e.cr.load('original');return m,e.cr.tokenizer(),meta
    m,t,p,meta=load()
    assert not hasattr(m.model.language_model.layers[31],'mhc_ffn')
    if kind=='edited':
        path=HERE/'checkpoints/candidate.pt';patch=torch.load(path,weights_only=True)
        assert patch['parent_sha256']==PARENT_HASH and patch['parameter']==PARAM
        assert tensor_hash(weight(m))==patch['parent_tensor_sha256']
        weight(m).copy_(patch['dense_weight']);assert tensor_hash(weight(m))==patch['written_tensor_sha256']
        meta['patch_sha256']=sha(path)
    meta['parent_sha256']=PARENT_HASH
    return m,t,meta
