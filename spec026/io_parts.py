"""Lossless gzip/torch checkpoints split below GitHub per-file limits."""
import gzip,hashlib,io,json,sys
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from supervised015.checkpoint import PartsWriter,PartsReader
H=ROOT/'spec026'
def save_json(path,m):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+'.tmp');q.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');q.replace(p)
def file_hash(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save_parts(folder,payload,meta):
 folder=Path(folder);assert not (folder/'manifest.json').exists(),'Never overwrite a model checkpoint';w=PartsWriter(folder)
 with gzip.GzipFile(fileobj=w,mode='wb',compresslevel=1,mtime=0) as z:torch.save(payload,z)
 w.close();m={'format':'gzip-torch-parts-v1','parts':w.parts,'compressed_sha256':w.hash.hexdigest(),'compressed_bytes':sum(x['bytes'] for x in w.parts),**meta};save_json(folder/'manifest.json',m);return m
def load_parts(folder):
 folder=Path(folder);m=json.loads((folder/'manifest.json').read_text());reader=PartsReader(folder,{'parts':m['parts']})
 with gzip.GzipFile(fileobj=reader,mode='rb') as z:raw=z.read()
 while reader.read(4*1024*1024):pass
 assert reader.hash.hexdigest()==m['compressed_sha256'];return torch.load(io.BytesIO(raw),map_location='cpu',weights_only=True),m

def load_draft(size,phase='inference'):
 from draft_model import DraftLM
 p,m=load_parts(H/'checkpoints'/size/phase);model=DraftLM(size,p['seed']);model.load_state_dict(p['model'],strict=True);del p
 if phase=='inference':model.inference_bf16()
 return model,m
