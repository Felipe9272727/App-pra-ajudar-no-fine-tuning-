"""Lossless XOR compression of the already-scored Native029 epoch02 snapshot."""
import hashlib,json,os,sys,time,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from android_epochs030.pack_source import PackSource
from native029.core import load_variant,torch,tensor_hash
HERE=ROOT/'android_epochs030';OUT=Path('/dev/shm/liquid-android/epochs030');HEADER=1024*1024
@torch.inference_mode()
def main():
    OUT.mkdir(parents=True,exist_ok=True);path=OUT/'epoch02.lspatch';assert not path.exists()
    started=time.monotonic();base=PackSource();model,tok,meta=load_variant('epoch02')
    params={n.removeprefix('model.language_model.'):p for n,p in model.named_parameters() if n.startswith('model.language_model.')}
    assert len(params)==546 and set(params)==set(base.manifest['tensors'])
    entries={};changed=0;raw_bytes=0
    with path.open('xb') as f:
        f.write(bytes(HEADER))
        for name,p in sorted(params.items()):
            old=base.manifest['tensors'][name];sha=tensor_hash(p)
            kind='f32' if p.dtype==torch.float32 else 'bf16';assert p.dtype in (torch.float32,torch.bfloat16)
            assert list(p.shape)==old['shape']
            spec={'shape':list(p.shape),'kind':kind,'sha256':sha,'base_sha256':old['source_sha256'],'changed':sha!=old['source_sha256']}
            if spec['changed']:
                raw=p.detach().contiguous().view(torch.uint8).numpy().tobytes()
                prior=bytes(len(raw)) if old['kind']=='zero' else base.read(old['offset'],old['bytes'])
                assert hashlib.sha256(prior).hexdigest()==old['source_sha256'] and len(prior)==len(raw)
                import numpy as np
                xor=np.bitwise_xor(np.frombuffer(raw,dtype=np.uint8),np.frombuffer(prior,dtype=np.uint8)).tobytes()
                packed=zlib.compress(xor,6)
                assert np.bitwise_xor(np.frombuffer(zlib.decompress(packed),dtype=np.uint8),np.frombuffer(prior,dtype=np.uint8)).tobytes()==raw
                spec.update(offset=f.tell(),compressed_bytes=len(packed),bytes=len(raw));f.write(packed)
                changed+=1;raw_bytes+=len(raw)
            entries[name]=spec
        manifest={'format':'liquid-sense-xor-patch-v1','variant':'native029_epoch02','source_archive_sha256':meta['checkpoint_sha256'],'base_checkpoint_sha256':base.manifest['source_checkpoint_sha256'],'base_pack_sha256':base.archive['pack']['sha256'],'tensor_count':546,'tensors':entries,'general_quality_promotion':False,'physical_layers':32,'executions':56}
        payload=json.dumps(manifest,separators=(',',':')).encode();assert len(payload)+16<HEADER
        f.seek(0);f.write(b'LSPATCH1'+len(payload).to_bytes(8,'little')+payload)
    with path.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
    report={'status':'exact_epoch02_patch_exported','path':str(path),'bytes':path.stat().st_size,'sha256':sha,'changed_tensors':changed,'decoded_override_bytes':raw_bytes,'all546_text_hashes_verified':True,'all699_source_hashes_verified':True,'source_archive_sha256':meta['checkpoint_sha256'],'no_quantization':True,'new_training_updates':0,'seconds':time.monotonic()-started}
    (HERE/'reports/patch_export.json').write_text(json.dumps(report,indent=2)+'\n')
    (HERE/'patch_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(report),flush=True)
if __name__=='__main__':main()
