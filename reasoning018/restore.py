import gzip,io,json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
HERE=ROOT/'reasoning018'
@tr.torch.inference_mode()
def load_candidate():
 model,tok,parent,meta=tr.load();audit=json.loads((HERE/'training_complete.json').read_text());data=(HERE/'checkpoints/candidate.pt.gz').read_bytes();assert hashlib.sha256(data).hexdigest()==audit['checkpoint_sha256'];raw=gzip.decompress(data);assert hashlib.sha256(raw).hexdigest()==audit['checkpoint_raw_sha256']
 payload=tr.torch.load(io.BytesIO(raw),weights_only=True);assert payload['parent_sha256']==tr.PARENT_HASH;params=dict(model.named_parameters())
 assert set(payload['parameters'])==set(json.loads((HERE/'trainable.json').read_text())['names'])
 for n,p in payload['parameters'].items():
  assert tr.tensor_hash(params[n])==audit['all_699_before'][n];params[n].copy_(p);assert tr.tensor_hash(params[n])==audit['all_699_after'][n]
 return model,tok,meta,audit
