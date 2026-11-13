"""Durable4MiB parts of exact old-APK fragments; no full APK duplication."""
import hashlib,io,json,re,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse022';SOURCE=HERE/'apk_archive';DEST=HERE/'archive_parts'
def create():
 assert not (DEST/'manifest.json').exists();DEST.mkdir(exist_ok=True)
 class Writer:
  def __init__(self):self.parts=[];self.buffer=bytearray();self.hash=hashlib.sha256()
  def write(self,data):
   self.hash.update(data);self.buffer.extend(data)
   while len(self.buffer)>=4194304:self.flush_part(4194304)
   return len(data)
  def flush_part(self,n):
   data=bytes(self.buffer[:n]);del self.buffer[:n];p=DEST/('part%04d.bin'%len(self.parts));p.write_bytes(data);self.parts.append({'path':p.name,'bytes':n,'sha256':hashlib.sha256(data).hexdigest()})
  def close(self):
   if self.buffer:self.flush_part(len(self.buffer))
 writer=Writer()
 with tarfile.open(fileobj=writer,mode='w|') as t:
  for p in sorted(SOURCE.iterdir()):
   assert re.fullmatch(r'[0-9a-f]{64}\.zlib|manifest\.json',p.name);t.add(p,arcname=p.name,recursive=False)
 writer.close();(DEST/'manifest.json').write_text(json.dumps({'format':'tar-parts-v1','parts':writer.parts,'stream_sha256':writer.hash.hexdigest(),'purpose':'lossless preservation of old signed general APKs','restore':'python tooluse022/pack_archive.py restore; python tooluse022/archive_apks.py restore --index 0'},indent=2)+'\n')
def restore():
 m=json.loads((DEST/'manifest.json').read_text());data=io.BytesIO();whole=hashlib.sha256()
 for item in m['parts']:
  b=(DEST/item['path']).read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'];whole.update(b);data.write(b)
 assert whole.hexdigest()==m['stream_sha256'];data.seek(0);SOURCE.mkdir(exist_ok=True)
 with tarfile.open(fileobj=data) as t:
  for member in t:
   assert member.isfile() and re.fullmatch(r'[0-9a-f]{64}\.zlib|manifest\.json',member.name)
   b=t.extractfile(member).read();p=SOURCE/member.name
   if p.exists():assert p.read_bytes()==b
   else:p.write_bytes(b)
if __name__=='__main__':
 import sys
 create() if sys.argv[1]=='create' else restore()
