"""Lossless archive of unused Android BUILD tools; no models or APKs selected."""
import hashlib,io,json,tarfile,os,sys,lzma
from pathlib import Path
H=Path(__file__).resolve().parent;BASE=Path('/dev/shm/liquid-android')
NAMES=['prebuilt','tools022/micropython-1.26.1','tools022/python-host','tools022/python-arm'];DEST=H/'build_tools_archive'

def digest(f):return hashlib.file_digest(f,'sha256').hexdigest()
def inventory():
    rows=[]
    for name in NAMES:
        for p in [BASE/name,*sorted((BASE/name).rglob('*'))]:
            rel=str(p.relative_to(BASE))
            assert not p.name.endswith(('.apk','.gguf','.safetensors','.pt')),'Model or APK must not be archived here'
            if p.is_symlink():rows.append({'path':rel,'kind':'link','target':os.readlink(p)})
            elif p.is_file():
                with p.open('rb') as f:sha=digest(f)
                rows.append({'path':rel,'kind':'file','bytes':p.stat().st_size,'sha256':sha})
            else:rows.append({'path':rel,'kind':'directory'})
    return rows
class Split(io.RawIOBase):
    def __init__(self):self.current=None;self.rows=[];self.hash=hashlib.sha256();self.size=0
    def writable(self):return True
    def write(self,b):
        view=memoryview(b);length=len(view)
        while view:
            if self.current is None:
                p=DEST/f'part{len(self.rows):04d}.bin';self.current=p.open('xb');self.rows.append({'path':p.name,'bytes':0})
            n=min(len(view),4194304-self.rows[-1]['bytes']);self.current.write(view[:n]);self.hash.update(view[:n]);self.rows[-1]['bytes']+=n;self.size+=n;view=view[n:]
            if self.rows[-1]['bytes']==4194304:self.current.close();self.current=None
        return length
    def finish(self):
        if self.current:self.current.close();self.current=None
        for r in self.rows:
            with (DEST/r['path']).open('rb') as f:r['sha256']=digest(f)
class Reader(io.RawIOBase):
    def __init__(self,parts):self.parts=iter(parts);self.f=None
    def readable(self):return True
    def read(self,n=-1):
        out=[];remaining=n
        while remaining:
            if self.f is None:
                try:p=next(self.parts)
                except StopIteration:break
                self.f=(DEST/p['path']).open('rb')
            b=self.f.read(remaining)
            if not b:self.f.close();self.f=None;continue
            out.append(b)
            if n>=0:remaining-=len(b)
        return b''.join(out)

def verify(m):
    assert inventory()==m['inventory'],'Build files changed since archive'
    seen={};full=hashlib.sha256()
    for p in m['parts']:
        with (DEST/p['path']).open('rb') as f:assert digest(f)==p['sha256']
        with (DEST/p['path']).open('rb') as f:
            while b:=f.read(1024*1024):full.update(b)
    assert full.hexdigest()==m['compressed_sha256']
    with tarfile.open(fileobj=Reader(m['parts']),mode='r|xz') as tar:
        for member in tar:
            if member.isfile():
                with tar.extractfile(member) as f:seen[member.name]={'path':member.name,'kind':'file','bytes':member.size,'sha256':digest(f)}
            elif member.issym():seen[member.name]={'path':member.name,'kind':'link','target':member.linkname}
            elif member.isdir():seen[member.name]={'path':member.name,'kind':'directory'}
            else:raise AssertionError('Unsupported archive entry')
    assert seen=={r['path']:r for r in m['inventory']},'Archive full contents differ'

def main():
    if '--reclaim' in sys.argv:
        m=json.loads((DEST/'manifest.json').read_text());assert (DEST/'remote_verified.json').exists();verify(m)
        for r in sorted(m['inventory'],key=lambda r:len(Path(r['path']).parts),reverse=True):
            p=BASE/r['path']
            if r['kind']=='directory':p.rmdir()
            else:p.unlink()
        (H/'reports/build_cache_reclaimed.json').write_text(json.dumps({'only_unused_Android_build_tools':NAMES,'all_files_preserved_in_verified_archive':True,'no_model_APK_checkpoint_or_experiment_removed':True,'freed_shm_file_bytes':sum(r.get('bytes',0) for r in m['inventory']),'archive_manifest':'native028/build_tools_archive/manifest.json'},indent=2)+'\n')
        print('BUILD_CACHE_RECLAIMED_VERIFIED',flush=True);return
    assert not DEST.exists() or not any(DEST.iterdir());DEST.mkdir(exist_ok=True);rows=inventory();writer=Split()
    with lzma.LZMAFile(writer,'w',preset=3) as compressed, tarfile.open(fileobj=compressed,mode='w|',dereference=False) as tar:
        # Explicit entries prevent inode hardlink substitution in the portable audit.
        for r in rows:
            tar.inodes={}
            member=tar.gettarinfo(str(BASE/r['path']),arcname=r['path'])
            if r['kind']=='file':
                with (BASE/r['path']).open('rb') as f:tar.addfile(member,f)
            else:tar.addfile(member)
    writer.finish();m={'format':'split-tar-xz-v1','inventory':rows,'parts':writer.rows,'compressed_sha256':writer.hash.hexdigest(),'compressed_bytes':writer.size,'source_roots':NAMES,'no_models_or_APKs':True}
    (DEST/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');verify(m)
    print('BUILD_ARCHIVE_VERIFIED',len(rows),writer.size,len(writer.rows),flush=True)
if __name__=='__main__':main()
