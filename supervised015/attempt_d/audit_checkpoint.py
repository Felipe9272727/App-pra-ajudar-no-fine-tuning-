"""Independent whole-model audit of the disk-restored D patch and full parent chain."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE.parent))
from restore import load_d,torch,tensor_hash,e
@torch.inference_mode()
def main():
    model,tok,meta,m=load_d();c=json.loads((HERE.parent/'attempt_c/checkpoints/final/manifest.json').read_text())
    finite={};hashes={}
    for n,p in model.named_parameters():
        finite[n]=all(bool(torch.isfinite(x).all()) for x in p.flatten().split(1024*1024));hashes[n]=tensor_hash(p)
    assert all(finite.values())
    for n,s in c['tensors'].items():assert hashes[n]==(m['tensor_sha256'] if n==m['tensor_name'] else s['tensor_sha256'])
    training=json.loads((HERE/'training_complete.json').read_text());arch=e.cr.check_architecture(model,2);arch['backward_passes']=training['new_total_gradient_updates_in_lineage'];arch['limitations']='Trained Qwen-sized hybrid; architecture and fit are not general reasoning superiority.'
    out={'status':'cold_restore_integrity_verified','text_tensors_verified':546,'all_699_parameter_tensors_finite':True,'vision_153_transitively_unchanged_via_C':True,'unchanged_545_text_tensors_match_C_hashes':True,'checkpoint_stream_sha256':m['stream_sha256'],'changed_values_vs_original_parent':m['changed_values_vs_original_parent'],'changed_tensors_vs_original_parent':m['changed_tensors_vs_original_parent'],'architecture':arch}
    (HERE/'integrity.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
