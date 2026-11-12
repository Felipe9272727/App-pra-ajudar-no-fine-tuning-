"""Post-training mechanical audit against E; no benchmark inference or fitting."""
import sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from balanced016.train import HERE,verify_frozen,save,torch,tensor_hash,family,e
from balanced016.restore import load_e,E_HASH
from supervised015 import checkpoint
@torch.inference_mode()
def main():
    verify_frozen();cfg=json.loads((HERE/'config.json').read_text());names=set(json.loads((HERE/'trainable.json').read_text())['names'])
    model,tok,meta,m=load_e();assert m['stream_sha256']==E_HASH
    params=dict(model.named_parameters());before_hash={n:tensor_hash(p) for n,p in params.items()};base={n:params[n].float().clone() for n in names}
    restored=checkpoint.restore(HERE/'checkpoints/final',model,E_HASH);details=[];frozen=[n for n in params if n not in names]
    assert len(frozen)==369 and all(tensor_hash(params[n])==before_hash[n] for n in frozen)
    for n in sorted(names):
        old=base[n];p=params[n];d=p.float()-old;den=max(float(old.norm()),math.sqrt(p.numel())*cfg['trust_rms_floor']);ratio=float(d.norm())/den
        item={'name':n,'family':family(n),'displacement_l2':float(d.norm()),'reference_l2_with_rms_floor':den,'relative_displacement':ratio,'configured_fp32_projection_radius':cfg['trust_relative'],'dtype':str(p.dtype),'changed_values':restored['tensors'][n]['changed_values']}
        if 'native_visit_gain' in n:
            item.update(before=old.tolist(),after=p.tolist());assert bool((p>0).all()) and abs(float(p.sum())-1)<1e-6
        details.append(item)
    for p in params.values():assert bool(torch.isfinite(p).all())
    save('weight_audit.json',{'status':'passed','checkpoint_stream_sha256':restored['stream_sha256'],'all_699_tensors_finite':True,'all_369_frozen_tensors_bitwise_unchanged':True,'all_546_text_hashes_verified_by_restore':True,'architecture':e.cr.check_architecture(model,2),'selected_details':details,'rounding_caveat':'Radius enforced in FP32 projection before BF16 storage; quantization and subsequent normalized gain projection can change the stored norm. Report actual values, not an exact BF16 guarantee.','actual_above_fp32_radius_tensors':[x['name'] for x in details if x['relative_displacement']>cfg['trust_relative']+1e-6],'quality_gain_measured_by_this_audit':False})
    print('WEIGHT_AUDIT_COMPLETE',restored['changed_tensors'],restored['changed_values'],flush=True)
if __name__=='__main__':main()
