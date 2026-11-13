"""Only official NDK headers, cached ZIP ranges instead of full664MB NDK."""
import hashlib,io,json,sys,urllib.request,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from android_chat.tools.fetch_android_tools import Remote
class CachedRemote(Remote):
 def __init__(self,*a):super().__init__(*a);self.cache={}
 def read(self,n=-1):
  if n<0:n=self.size-self.pos
  n=min(n,self.size-self.pos);parts=[]
  while n:
   start=(self.pos//1048576)*1048576
   if start not in self.cache:
    saved=self.pos;self.pos=start;self.cache[start]=super().read(min(1048576,self.size-start));self.pos=saved
   block=self.cache[start];off=self.pos-start;piece=block[off:off+n];parts.append(piece);self.pos+=len(piece);n-=len(piece)
  return b''.join(parts)
def main():
 url='https://dl.google.com/android/repository/android-ndk-r27c-linux.zip';r=CachedRemote(url,663987688);dest=Path('/dev/shm/liquid-android/tooling/android/sysroot/include');records=[]
 prefix='android-ndk-r27c/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/include/'
 with zipfile.ZipFile(r) as z:
  for i in z.infolist():
   if not i.filename.startswith(prefix) or i.is_dir():continue
   rel=i.filename.removeprefix(prefix)
   if rel.startswith(('arm-linux-androideabi/','i686-linux-android/','x86_64-linux-android/','riscv64-linux-android/')):continue
   b=z.read(i);p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);records.append({'path':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 (ROOT/'tooluse022/reports/ndk_headers.json').write_text(json.dumps({'source':url,'zip_CRCs_verified':True,'records':records},indent=2)+'\n');print('HEADERS',len(records),'cached_ranges',len(r.cache),flush=True)
if __name__=='__main__':main()
