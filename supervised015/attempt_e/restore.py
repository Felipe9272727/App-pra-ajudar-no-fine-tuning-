"""Restore the exact C model, then the small raw-BF16 D matrix patch."""
import sys,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE.parent))
from train_runtime import load,e,torch,PARENT_HASH,tensor_hash
import checkpoint
BH='c2f851b064b9656e356fe2c37985df88d598bf2fd358903d1a06fcf53b659ca7';CH='05687b52a1efb934cec6d5f7ce4c63b62969dd88cec1c2f85364c0afac1cbb15'
@torch.inference_mode()
def load_d():
    model,tok,parent,meta=load();b=checkpoint.restore(HERE.parent/'attempt_b/checkpoints/final',model,PARENT_HASH);assert b['stream_sha256']==BH
    c=checkpoint.restore(HERE.parent/'attempt_c/checkpoints/final',model,BH);assert c['stream_sha256']==CH
    manifest=json.loads((HERE/'checkpoints/candidate/manifest.json').read_text());assert manifest['parent_specialist_stream_sha256']==CH
    tensor=dict(model.named_parameters())[manifest['tensor_name']];assert tensor_hash(tensor)==manifest['parent_tensor_sha256']
    assert list(tensor.shape)==manifest['shape'] and str(tensor.dtype)==manifest['dtype']
    dest=tensor.view(torch.uint8).flatten();offset=0;whole=hashlib.sha256()
    for part in manifest['parts']:
        data=(HERE/'checkpoints/candidate'/part['path']).read_bytes();assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256'];whole.update(data)
        dest[offset:offset+len(data)].copy_(torch.frombuffer(bytearray(data),dtype=torch.uint8));offset+=len(data)
    assert offset==len(dest)==manifest['bytes'] and whole.hexdigest()==manifest['stream_sha256'];assert tensor_hash(tensor)==manifest['tensor_sha256']
    return model,tok,meta,manifest
