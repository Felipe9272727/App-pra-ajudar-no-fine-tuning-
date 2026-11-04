"""Recover original Qwen tensors from our untrained, exactly scaled v1 port.

Only needed when the large upstream download is unavailable. The saved port
copies all source tensors; its output matrices are divided by powers of two.
No estimated inversion or model fitting is used here.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import torch
from safetensors import safe_open
from safetensors.torch import save_file

ROOT=Path(__file__).resolve().parents[1]


@torch.inference_mode()
def main():
    torch.set_num_threads(4)
    manifest=json.loads((ROOT/'sensenova_port/surgery_manifest.json').read_text())
    assert manifest['training_steps']==0 and manifest['backward_passes']==0
    sources=manifest['source_layer_for_each_physical_layer']
    visits=Counter(sources[i] for i in manifest['execution_plan'])
    assert all(x>0 and x&(x-1)==0 for x in visits.values())
    result={};duplicates=0
    with safe_open(ROOT/'sensenova_port/model.safetensors',framework='pt',device='cpu') as f:
        for name in f.keys():
            match=re.fullmatch(r'model\.language_model\.layers\.(\d+)\.(.*)',name)
            if not match:
                result[name]=f.get_tensor(name);continue
            physical=int(match[1]);suffix=match[2]
            if suffix.startswith('mhc_'):continue
            source=sources[physical];key=f'model.language_model.layers.{source}.{suffix}'
            value=f.get_tensor(name)
            if suffix in ['mlp.down_proj.weight','self_attn.o_proj.weight','linear_attn.out_proj.weight']:
                value=(value.float()*visits[source]).to(value.dtype)
                assert torch.equal((value.float()/visits[source]).to(value.dtype),f.get_tensor(name)),name
            if key in result:
                assert torch.equal(result[key],value),key
                duplicates+=1
            else:result[key]=value.contiguous()
        index=json.loads((ROOT/'upstream/model.safetensors.index.json').read_text())
        assert set(result)==set(index['weight_map']),'Recovered checkpoint keys must match the pinned original index'
        count=sum(t.numel() for t in result.values())
        assert count==873438784,count
        target=ROOT/'upstream/model.safetensors-00001-of-00001.safetensors'
        save_file(result,target,metadata={'format':'pt'})
    digest=hashlib.sha256()
    with target.open('rb') as f:
        while block:=f.read(8*1024*1024):digest.update(block)
    official=None
    meta=ROOT.parent/'qwen_integrity_meta.json'
    if meta.exists():
        info=json.loads(meta.read_text())
        for s in info.get('siblings',[]):
            if s.get('rfilename')==target.name:official=s.get('lfs',{}).get('sha256')
    record={'method':'invert exact power-of-two v1 output scaling; restore all 24 source layers',
        'source_port':'saved v1 untrained checkpoint','tensor_elements':count,
        'duplicate_source_tensors_verified':duplicates,'file_sha256':digest.hexdigest(),
        'official_file_sha256':official,'byte_identical_to_official':official==digest.hexdigest() if official else None,
        'base_revision':'2fc06364715b967f1860aea9cf38778875588b17','backward_passes':0}
    (ROOT/'v3_experiment/original_recovery.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record,indent=2),flush=True)


if __name__=='__main__':main()
