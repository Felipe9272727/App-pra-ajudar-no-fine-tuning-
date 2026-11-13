"""025 exact selected-parameter overlays and identical evaluation settings."""
import gc,gzip,hashlib,io,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'loop025'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
from train_runtime import torch

def save(name,data):tr.e.cr.atomic_json(HERE/name,data)
def read(name):return json.loads((HERE/name).read_text())
def hashfile(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def family(n):
 if n in read('trainable.json')['exit_names']:return 'opened_loop_exit'
 if '.mhc_' in n:return 'mhc'
 if 'native_visit_gain' in n:return 'loop_gain'
 if any(s in n for s in ['.in_proj_a.','.in_proj_b.','.conv1d.','.A_log','.dt_bias']):return 'temporal'
 return 'normalization'
def memory():
 s=Path('/proc/self/status').read_text();return {k:int(s.split(label+':')[1].split()[0]) for k,label in [('rss_kb','VmRSS'),('peak_rss_kb','VmHWM')]}
def verify():
 for n,h in read('frozen.json').items():assert hashfile(ROOT/n)==h,n

def payload_epoch(epoch):
 folder=HERE/'checkpoints'/f'epoch{epoch:02d}';m=json.loads((folder/'manifest.json').read_text());h=hashlib.sha256();compressed=io.BytesIO()
 for x in m['parts']:
  b=(folder/x['path']).read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];h.update(b);compressed.write(b)
 assert h.hexdigest()==m['compressed_sha256'];compressed.seek(0)
 with gzip.GzipFile(fileobj=compressed,mode='rb') as z:data=torch.load(io.BytesIO(z.read()),weights_only=True,map_location='cpu')
 assert data['parent_sha256']==tr.PARENT_HASH and data['step']==epoch*8
 return data,m

@torch.inference_mode()
def load_variant(variant):
 if variant=='original':
  model,meta=tr.e.cr.load('original');tok=tr.e.cr.tokenizer()
 else:
  model,tok,parent,meta=tr.load();del parent
  if variant!='parent':
   epoch=int(variant.removeprefix('epoch'));data,manifest=payload_epoch(epoch);ps=dict(model.named_parameters());audit=read(f'reports/epoch{epoch:02d}.json')
   assert set(data['parameters'])==set(read('trainable.json')['names'])
   for n,p in data['parameters'].items():ps[n].copy_(p)
   assert all(tr.tensor_hash(p)==audit['all_699_after'][n] for n,p in ps.items()),'Cold-restored weight mismatch'
   meta={**meta,'epoch':epoch,'checkpoint_sha256':manifest['compressed_sha256']};del data;gc.collect()
 torch.set_num_threads(4);model.eval();model.requires_grad_(False);return model,tok,meta

def encode(tok,row):
 ids=tr.e.cr.prompt(tok,row['prompt'],thinking=False);gold=torch.tensor(tok.encode(row['solution'],add_special_tokens=False)+[248046]);assert ids.shape[1]+len(gold)<384
 seq=torch.cat([ids,gold.view(1,-1)],1);return seq[:,:-1],gold

def export_epoch(path,epoch,audit):
 folder=HERE/'checkpoints'/f'epoch{epoch:02d}';assert not (folder/'manifest.json').exists(),'Immutable epoch already exported';folder.mkdir(parents=True,exist_ok=True);parts=[];whole=hashlib.sha256();size=0
 with Path(path).open('rb') as f:
  while b:=f.read(4*1024*1024):
   n=f'part{len(parts):04d}.bin';(folder/n).write_bytes(b);parts.append({'path':n,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()});whole.update(b);size+=len(b)
 assert whole.hexdigest()==hashfile(path)
 m={'format':'gzip-torch-selected-parameters-with-optimizer-parts-v1','parent_sha256':tr.PARENT_HASH,'epoch':epoch,'step':epoch*8,'parts':parts,'compressed_bytes':size,'compressed_sha256':whole.hexdigest(),'selected_tensors':292,'selected_values':48340208,'optimizer_RNG_included':True};(folder/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');audit['checkpoint']=m;save(f'reports/epoch{epoch:02d}.json',audit);return m
