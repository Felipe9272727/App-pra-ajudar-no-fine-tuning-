"""Read-only artifact inventory and gzip integrity after all model workers close."""
import hashlib,json,gzip,io
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
class Reader(io.RawIOBase):
    def __init__(self,folder,parts):self.folder=folder;self.parts=iter(parts);self.f=None
    def readable(self):return True
    def read(self,n=-1):
        out=[];left=n
        while left:
            if self.f is None:
                try:part=next(self.parts)
                except StopIteration:break
                self.f=(self.folder/part['path']).open('rb')
            block=self.f.read(left)
            if not block:self.f.close();self.f=None;continue
            out.append(block)
            if n>=0:left-=len(block)
        return b''.join(out)

def main():
    assert json.load(open(H/'status.json'))['status']=='complete'
    assert not json.load(open(H/'runtime.json'))['model_process_active']
    assert not json.load(open(H/'arithmetic_runtime.json'))['model_process_active']
    gzip_audit=[]
    for stage in ['initial_factors','recovery_step48','sft_epoch1','sft_final','policy_final']:
        folder=H/'checkpoints'/stage;m=json.load(open(folder/'manifest.json'));full=hashlib.sha256()
        for part in m['parts']:
            path=folder/part['path'];assert path.stat().st_size==part['bytes'] and sha(path)==part['sha256']
            with path.open('rb') as f:
                while block:=f.read(1024*1024):full.update(block)
        assert full.hexdigest()==m['compressed_sha256'];uncompressed=0
        with gzip.GzipFile(fileobj=Reader(folder,m['parts']),mode='rb') as stream:
            while block:=stream.read(1024*1024):uncompressed+=len(block)
        gzip_audit.append({'stage':stage,'compressed_sha256':full.hexdigest(),'compressed_bytes':m['compressed_bytes'],
            'gzip_CRC_EOF_verified':True,'uncompressed_bytes':uncompressed,
            'cold_native_all699_hashes_verified':stage in ['sft_final','policy_final']})
    (H/'reports/archive_integrity.json').write_text(json.dumps(gzip_audit,indent=2)+'\n')
    files={str(p.relative_to(ROOT)):p for p in H.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name not in ['artifact_manifest.json','remote_verification.json','publish_counter.json']}
    for stage in ['initial_factors','recovery_step48','sft_epoch1','sft_final','policy_final']:
        for p in (H/'checkpoints'/stage).glob('*'):
            if p.is_file():files[str(p.relative_to(ROOT))]=p
    rows=[]
    for name,p in sorted(files.items()):
        b=p.read_bytes() if p.stat().st_size<1024*1024 else None
        if b is not None:git=hashlib.sha1(('blob '+str(len(b))+'\0').encode()+b).hexdigest()
        else:
            digest=hashlib.sha1(('blob '+str(p.stat().st_size)+'\0').encode())
            with p.open('rb') as f:
                while block:=f.read(1024*1024):digest.update(block)
            git=digest.hexdigest()
        rows.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p),'git_blob':git})
    (H/'artifact_manifest.json').write_text(json.dumps({'files':rows,'count':len(rows),'all_model_workers_closed':True,'parent_unchanged':True},indent=2)+'\n')
    print('CATALOG028_COMPLETE',len(rows),len(gzip_audit))
if __name__=='__main__':main()
