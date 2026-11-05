"""Lossless archive of the actual observations; no model is loaded."""
from pathlib import Path
import hashlib,json,tarfile,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
 files=sorted((HERE/'activations').glob('*.pt'))+[HERE/'all_coordinate_moments.pt'];assert len(files)==8
 rows=[{'path':str(p.relative_to(HERE)),'bytes':p.stat().st_size,'sha256':digest(p)} for p in files]
 out=HERE/'activation_archive.tar.xz';start=time.monotonic()
 with tarfile.open(out,'w:xz',preset=6) as archive:
  for path in files:archive.add(path,arcname=str(path.relative_to(HERE)),recursive=False)
 folder=HERE/'activation_archive';folder.mkdir(exist_ok=True);chunks=[]
 with out.open('rb') as f:
  index=0
  while data:=f.read(8*1024*1024):
   p=folder/f'part_{index:03d}.bin';p.write_bytes(data);chunks.append({'path':str(p.relative_to(ROOT)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()});index+=1
 manifest={'format':'concatenate sequential parts into activation_archive.tar.xz; restore with restore_traces.py',
  'archive_sha256':digest(out),'archive_bytes':out.stat().st_size,'uncompressed_bytes':sum(r['bytes'] for r in rows),
  'members':rows,'chunks':chunks,'seconds':time.monotonic()-start,'lossless_actual_dtype':True}
 (HERE/'activation_archive.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in manifest.items() if k not in ['members','chunks']}));print('CHUNKS',len(chunks))
if __name__=='__main__':main()
