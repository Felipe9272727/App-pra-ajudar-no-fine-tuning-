"""Verify exact step48 state and actual BF16 merge bounds without model loading."""
import sys,json,math,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'native028'))
import core
from safetensors import safe_open
from torch import nn
T=core.torch;T.set_num_threads(4);H=ROOT/'native028'
state=T.load('/dev/shm/liquid-native028/rolling_sft.pt',weights_only=True)
assert state['step']==48 and state['extra']['sft_tokens']==2699
# Preserve the exact pre-export optimization state before resumption.
folder=H/'checkpoints/recovery_step48'
manifest=core.read('checkpoints/recovery_step48/manifest.json') if (folder/'manifest.json').exists() else core.save_parts(folder,state,{'phase':'sft_recovery_before_export','steps':48,'parent_sha256':core.tr.PARENT_HASH,'optimizer_RNG_included':True})
restored,_=core.load_parts(folder)
checked=[0]
def equal(a,b):
    if T.is_tensor(a):assert T.equal(a,b);checked[0]+=1
    elif isinstance(a,dict):
        assert set(a)==set(b)
        for k in a:equal(a[k],b[k])
    elif isinstance(a,(tuple,list)):
        assert len(a)==len(b)
        for x,y in zip(a,b):equal(x,y)
    else:assert a==b

equal(state,restored);del restored
before=core.read('reports/preflight.json')['all699_parent_hashes']
sources=[4*g+i for g in [0,1,1,2,3,3,4,5] for i in range(4)]
identity=set(range(8,12))|set(range(20,24));results=[]
with safe_open(ROOT/'upstream/model.safetensors-00001-of-00001.safetensors',framework='pt',device='cpu') as sf:
    for name,b in state['factors'].items():
        if not name.endswith('.lora_B'):continue
        prefix=name[:-len('.lora_B')];physical=int(prefix.split('.')[3]);suffix='.'.join(prefix.split('.')[4:])+'.weight'
        w=sf.get_tensor(f'model.language_model.layers.{sources[physical]}.{suffix}')
        if physical in identity and suffix in ['mlp.down_proj.weight','linear_attn.out_proj.weight','self_attn.o_proj.weight']:w=(w.float()*0).to(w.dtype)
        assert core.tensor_hash(w)==before[prefix+'.weight'],prefix
        a=state['factors'][prefix+'.lora_A'];den=max(float(w.double().norm()),math.sqrt(w.numel())*.01);cap=.01*den
        delta=b@a;base=w.float();pre=float(((base+delta).to(w.dtype).float()-base).double().norm())
        old=pre
        if pre>cap+1e-7:
            lo=0.;hi=1.
            for _ in range(24):
                mid=(lo+hi)/2
                if float(((base+delta*mid).to(w.dtype).float()-base).double().norm())<=cap:lo=mid
                else:hi=mid
            old=float(((base+(b*lo)@a).to(w.dtype).float()-base).double().norm())
        m=core.LowRankLinear.__new__(core.LowRankLinear);nn.Module.__init__(m)
        m.weight=nn.Parameter(w,requires_grad=False);m.bias=None
        m.lora_A=nn.Parameter(a.clone());m.lora_B=nn.Parameter(b.clone());m._lora_reference_denom=den
        root=nn.Module();root.add_module('projection',m);events=core.project(root,{}, {}, {},export=True)
        actual=float(((base+m.lora_B@m.lora_A).to(w.dtype).float()-base).double().norm())
        assert actual<=cap+1e-7
        results.append({'name':prefix,'cap':cap,'old_merged_norm':old,'old_exceeded':old>cap+1e-7,
            'corrected_merged_norm':actual,'corrected_within_bound':True})
        del m,root,w,base,delta
core.save('recovery/export_fix/verification.json',{'step48_exact_tensor_state_checks':checked[0],
    'step':state['step'],'target_tokens':state['extra']['sft_tokens'],'rolling_raw_sha256':core.file_hash('/dev/shm/liquid-native028/rolling_sft.pt'),
    'recovery_checkpoint':manifest,'reconstructed_all150_base_projection_hashes_match':True,
    'old_bound_violations':sum(r['old_exceeded'] for r in results),'all150_fixed_bounds_pass':len(results)==150,
    'checks':results,'optimizer_updates_repeated':0,'quality_test_outputs_seen':0})
print('RECOVERY028_VERIFIED',checked[0],len(results),sum(r['old_exceeded'] for r in results),flush=True)
