"""Minimal official Android build tools/sysroot using verified ZIP entries over HTTPS."""
import io,zipfile,urllib.request,os,json,hashlib,argparse
from pathlib import Path
BASE='https://dl.google.com/android/repository/'
class Remote(io.RawIOBase):
 def __init__(self,url,size):self.url=url;self.size=size;self.pos=0
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,pos,whence=0):self.pos=pos if whence==0 else (self.pos+pos if whence==1 else self.size+pos);return self.pos
 def read(self,n=-1):
  if n<0:n=self.size-self.pos
  n=min(n,self.size-self.pos)
  if n<=0:return b''
  req=urllib.request.Request(self.url,headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'})
  with urllib.request.urlopen(req,timeout=60) as r:
   if r.status!=206:raise RuntimeError('Server did not honor range; refusing whole NDK download')
   b=r.read()
  assert len(b)==n;self.pos+=len(b);return b

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);records=[]
 def write(z,member,dest):
  data=z.read(member);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  if dest.name in ['aapt2','zipalign']:dest.chmod(0o755)
  records.append({'source':member,'dest':str(dest.relative_to(a.out)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 for name,expected,selected in [
  ('platform-35_r02.zip','0bb560a90a7a2cbd0dd8348224d518b638fe7949',lambda n:n.endswith('/android.jar')),
  ('build-tools_r35_linux.zip','2cfaa0bbb2336e9ec18ed3ecea84fa2e2af607bc',lambda n:n.endswith(('/aapt2','/zipalign','/lib/d8.jar','/lib/apksigner.jar','/lib64/libc++.so'))),
 ]:
  archive=a.out/name;urllib.request.urlretrieve(BASE+name,archive);assert hashlib.sha1(archive.read_bytes()).hexdigest()==expected
  with zipfile.ZipFile(archive) as z:
   for n in z.namelist():
    if selected(n):write(z,n,a.out/('platform/android.jar' if n.endswith('/android.jar') else 'build-tools/'+n.split('/',1)[1]))
  archive.unlink()
 remote=Remote(BASE+'android-ndk-r27c-linux.zip',663987688)
 with zipfile.ZipFile(remote) as z:
  prefix='android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/aarch64-linux-android/'
  for n in z.namelist():
   if n.endswith('/aarch64/libunwind.a'):
    write(z,n,a.out/'sysroot/libunwind.a')
   if n.startswith(prefix):
    rel=n.removeprefix(prefix)
    if rel.startswith('28/') and rel.endswith(('.so','.o')) or rel=='libunwind.a':write(z,n,a.out/'sysroot'/rel)
 (a.out/'tool_sources.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps({'files':len(records),'bytes':sum(r['bytes'] for r in records)}))
if __name__=='__main__':main()
