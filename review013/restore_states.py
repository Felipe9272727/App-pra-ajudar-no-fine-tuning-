"""Reconstruct exact teaching artifacts from hash-checked archive parts."""
import hashlib,io,json,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    manifest=json.loads((HERE/'archives/manifest.json').read_text());parts=[]
    for p in manifest['parts']:
        b=(HERE/p['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==p['sha256'];parts.append(b)
    data=b''.join(parts);assert hashlib.sha256(data).hexdigest()==manifest['sha256']
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:xz') as tar:
        members=tar.getmembers();assert {p.name for p in members}==set(manifest['members'])
        for p in members:
            assert p.isfile() and p.name.startswith('states/') and '..' not in Path(p.name).parts
            b=tar.extractfile(p).read();assert hashlib.sha256(b).hexdigest()==manifest['members'][p.name]['sha256']
            dest=HERE/p.name
            if dest.exists():assert dest.read_bytes()==b,'refuse overwriting different observed state'
            else:dest.parent.mkdir(exist_ok=True);dest.write_bytes(b)
    print('120 EXACT TEACHING ARTIFACTS VERIFIED/RESTORED')
if __name__=='__main__':main()
