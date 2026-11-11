"""Verify/reconstruct archived activations; never overwrite different bytes."""
import hashlib,io,json,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    m=json.loads((HERE/'archives/manifest.json').read_text());parts=[]
    for p in m['parts']:
        b=(HERE/p['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==p['sha256'];parts.append(b)
    data=b''.join(parts);assert hashlib.sha256(data).hexdigest()==m['sha256']
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:xz') as tar:
        assert {p.name for p in tar.getmembers()}==set(m['members'])
        for p in tar.getmembers():
            assert p.isfile() and p.name.startswith('states/') and '..' not in Path(p.name).parts
            b=tar.extractfile(p).read();assert hashlib.sha256(b).hexdigest()==m['members'][p.name]['sha256']
            dest=HERE/p.name
            if dest.exists():assert dest.read_bytes()==b
            else:dest.parent.mkdir(exist_ok=True);dest.write_bytes(b)
    print('ALL NINE CONSTRUCTION STATES VERIFIED/RESTORED EXACTLY')
if __name__=='__main__':main()
