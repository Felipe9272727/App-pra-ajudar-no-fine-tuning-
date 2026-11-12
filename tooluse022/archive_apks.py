"""Lossless deduplication of old signed APKs; never discard an unverified byte.

Model tensor payloads reference immutable safetensors already in this project.
All unmatched bytes, ZIP structures, signing blocks and padding are compressed.
Both complete APK hashes are reconstructed BEFORE optional removal of build copies.
"""
import argparse,hashlib,json,struct,zlib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'tooluse022/apk_archive'
APKS=[('/dev/shm/liquid-android/apk/LiquidSense-0.1.0-preview.apk','9e0d4d58e3730d67a02afbad0ef6d4f796147963b7fc8222643be0fabbcadebe'),('/dev/shm/liquid-android/fast020-apk/LiquidSense-0.1.1-speed-preview.apk','3a8eab346270899706671c04bf900f0061fc713b798baf768c079063fa793bef')]
CHUNK=4*1024*1024
def region(path,offset,length):
 with Path(path).open('rb') as f:
  f.seek(offset)
  while length:
   b=f.read(min(length,CHUNK));assert b,'truncated immutable backing file';length-=len(b);yield b
def digest(parts):
 h=hashlib.sha256()
 for b in parts:h.update(b)
 return h.hexdigest()
def saveblock(data):
 h=hashlib.sha256(data).hexdigest();p=DEST/(h+'.zlib')
 if not p.exists():p.write_bytes(zlib.compress(data,9))
 return {'compressed':p.name,'bytes':len(data),'sha256':h}
def materialize(spec):
 if 'source' in spec:yield from region(ROOT/spec['source'],spec['offset'],spec['bytes'])
 else:
  data=zlib.decompress((DEST/spec['compressed']).read_bytes());assert len(data)==spec['bytes'];yield data
def verified(spec):
 h=hashlib.sha256()
 for b in materialize(spec):h.update(b);yield b
 assert h.hexdigest()==spec['sha256'],spec
def model_parts(man):
 for spec in man['pack']['parts']:yield from verified(spec)
def apk_parts(man,item):
 yield from verified(item['prefix']);yield from model_parts(man);yield from verified(item['suffix'])
def create():
 DEST.mkdir(parents=True,exist_ok=True);assert not (DEST/'manifest.json').exists(),'Archive already exists; verify/restore instead'
 source=ROOT/'sensenova_port/model.safetensors';index={}
 with source.open('rb') as f:
  n=struct.unpack('<Q',f.read(8))[0];header=json.loads(f.read(n));base=8+n
 for key,spec in header.items():
  if key=='__metadata__':continue
  a,b=spec['data_offsets'];h=digest(region(source,base+a,b-a));index[(h,b-a)]={'source':str(source.relative_to(ROOT)),'offset':base+a,'bytes':b-a,'sha256':h}
 print('INDEXED',len(index),flush=True)
 p=Path(APKS[0][0])
 with zipfile.ZipFile(p) as z:
  info=z.getinfo('assets/model.lsp');assert info.compress_type==0
 with p.open('rb') as f:
  f.seek(info.header_offset);head=f.read(30);name,extra=struct.unpack_from('<HH',head,26);offset=info.header_offset+30+name+extra
  f.seek(offset);assert f.read(8)==b'LSENSE01';n=struct.unpack('<Q',f.read(8))[0];pack_manifest=json.loads(f.read(n))
 specs=sorted({(v['offset'],v['bytes']) for v in pack_manifest['tensors'].values() if v['bytes']})
 parts=[];position=0;unmatched=0
 for start,size in specs+[(info.file_size,0)]:
  assert start>=position,(position,start)
  if start>position:parts.append(saveblock(b''.join(region(p,offset+position,start-position))))
  if size:
   h=digest(region(p,offset+start,size));ref=index.get((h,size))
   if ref:parts.append(ref)
   else:
    unmatched+=size;assert size<160*1024*1024,'Large unmatched tensor; stop without removing anything'
    parts.append(saveblock(b''.join(region(p,offset+start,size))))
   position=start+size
 man={'format':'exact-signed-apk-dedup-v1','pack':{'bytes':info.file_size,'sha256':digest(region(p,offset,info.file_size)),'parts':parts},'apks':[],'immutable_sources_do_not_remove':['sensenova_port/model.safetensors'],'unmatched_raw_bytes':unmatched}
 for name,expected in APKS:
  path=Path(name)
  with zipfile.ZipFile(path) as z:i=z.getinfo('assets/model.lsp');assert i.compress_type==0
  with path.open('rb') as f:f.seek(i.header_offset);h=f.read(30)
  a=i.header_offset+30+sum(struct.unpack_from('<HH',h,26));assert i.file_size==info.file_size
  assert digest(region(path,a,i.file_size))==man['pack']['sha256']
  item={'path':name,'bytes':path.stat().st_size,'sha256':expected,'prefix':saveblock(b''.join(region(path,0,a))),'suffix':saveblock(b''.join(region(path,a+i.file_size,path.stat().st_size-a-i.file_size)))}
  assert digest(apk_parts(man,item))==expected,'Full reconstructed signature-bearing APK must match'
  assert digest(region(path,0,path.stat().st_size))==expected
  man['apks'].append(item);print('EXACT_RECONSTRUCTION',path.name,expected,flush=True)
 man['archive_payload_bytes']=sum(x.stat().st_size for x in DEST.glob('*.zlib'));assert man['archive_payload_bytes']<90*1024*1024
 (DEST/'manifest.json').write_text(json.dumps(man,indent=2)+'\n');print('ARCHIVE_COMPLETE',man['archive_payload_bytes'],flush=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['create','verify','retire-build-copies','restore']);ap.add_argument('--index',type=int,choices=[0,1]);args=ap.parse_args()
 if args.action=='create':return create()
 man=json.loads((DEST/'manifest.json').read_text());assert digest(model_parts(man))==man['pack']['sha256']
 for i,item in enumerate(man['apks']):
  if args.index is not None and i!=args.index:continue
  if args.action=='restore':
   path=Path(item['path']);assert not path.exists(),'Never overwrite an existing APK';path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.restoring')
   with tmp.open('xb') as f:
    for b in apk_parts(man,item):f.write(b)
   assert digest(region(tmp,0,tmp.stat().st_size))==item['sha256'];tmp.rename(path)
  else:
   assert digest(apk_parts(man,item))==item['sha256']
   if args.action=='retire-build-copies':
    p=Path(item['path'])
    if p.exists():assert digest(region(p,0,p.stat().st_size))==item['sha256'];p.unlink()
  print('VERIFIED',i,item['sha256'],flush=True)
if __name__=='__main__':main()
