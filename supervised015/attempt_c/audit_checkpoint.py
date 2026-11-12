"""Independent cold restore, finiteness and unchanged-vision audit; no generation."""
import sys,json,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from train_runtime import load,e,torch,PARENT_HASH,text_parameter,tensor_hash
import checkpoint
HERE=Path(__file__).resolve().parent
@torch.inference_mode()
def main():
    model,_,_,meta=load()
    base=checkpoint.restore(HERE.parent/'attempt_b/checkpoints/final',model,PARENT_HASH)
    assert base['stream_sha256']=='c2f851b064b9656e356fe2c37985df88d598bf2fd358903d1a06fcf53b659ca7'
    before={n:tensor_hash(p) for n,p in model.named_parameters()}
    manifest=checkpoint.restore(HERE/'checkpoints/final',model,base['stream_sha256'])
    finite={};after={};router_weights={};gains={}
    for n,p in model.named_parameters():
        finite[n]=all(bool(torch.isfinite(c).all()) for c in p.detach().flatten().split(1024*1024))
        after[n]=tensor_hash(p)
        if '.mhc_' in n and n.endswith('.weight'):router_weights[n]=float(p.float().norm())
        if n.endswith('.native_visit_gain'):gains[n]=p.tolist()
    assert all(finite.values()),'Nonfinite checkpoint weight'
    assert all(after[n]==h for n,h in before.items() if not text_parameter(n))
    assert all(after[n]==t['tensor_sha256'] and before[n]==t['parent_tensor_sha256'] for n,t in manifest['tensors'].items())
    report={'status':'cold_restore_integrity_verified','checkpoint_stream_sha256':manifest['stream_sha256'],
        'all_699_parameter_tensors_finite':True,'text_tensors_verified':len(manifest['tensors']),
        'vision_tensors_bitwise_unchanged':sum(not text_parameter(n) for n in before),
        'changed_text_tensors':sum(before[n]!=after[n] for n in before if text_parameter(n)),
        'router_input_weights_nonzero':sum(v>0 for v in router_weights.values()),
        'router_input_weight_l2':router_weights,'loop_visit_gains':gains,
        'architecture':e.cr.check_architecture(model,2),'parent_sha256':PARENT_HASH,
        'mechanical_architecture_and_finiteness_are_not_a_reasoning_quality_claim':True}
    training=json.loads((HERE/'training_complete.json').read_text())
    report['architecture']['backward_passes']=training['backward_passes']
    report['parent_specialist_stream_sha256']=base['stream_sha256']
    report['changed_text_tensors_vs_original_parent']=training['changed_tensors_vs_original_parent']
    report['changed_values_vs_original_parent']=training['changed_values_vs_original_parent']
    report['architecture']['limitations']='Qwen widths; trained Loop/mHC and Liquid-inspired operators, not full SenseNova/LFM3; architecture is not a quality claim.'
    (HERE/'integrity.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['router_input_weight_l2','loop_visit_gains','architecture']}),flush=True)
if __name__=='__main__':main()
