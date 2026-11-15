"""Standard-library exact APK restoration on CI; no model framework or private keys."""
import argparse,hashlib,json,sys,urllib.request,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'android_install033'
def read(path):return json.loads((ROOT/path).read_text())
def file_blocks(path,offset=0,length=None):
    with path.open('rb') as f:
        f.seek(offset)
        while length is None or length:
            raw=f.read(4*1024*1024 if length is None else min(length,4*1024*1024))
            if not raw:assert length is None;break
            if length is not None:length-=len(raw)
            yield raw
def hashfile(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def download_upstream():
    source=read('android_install033/portable_sources.json');out=ROOT/'upstream/model.safetensors-00001-of-00001.safetensors';out.parent.mkdir(exist_ok=True)
    if not out.exists():
        url=f"https://huggingface.co/Qwen/Qwen3.5-0.8B/resolve/{source['upstream_revision']}/{out.name}"
        temp=out.with_suffix('.downloading');urllib.request.urlretrieve(url,temp);assert hashfile(temp)==source['upstream_sha256'];temp.rename(out)
    assert hashfile(out)==source['upstream_sha256']
def pack_blocks():
    inline=read('android_install033/portable_sources.json')['inline_source_bytes_by_SHA256'];m=read('tooluse022/apk_archive/manifest.json')
    for p in m['pack']['parts']:
        if p['sha256'] in inline:chunks=[bytes.fromhex(inline[p['sha256']])]
        elif 'source'in p:chunks=file_blocks(ROOT/p['source'],p['offset'],p['bytes'])
        else:chunks=[zlib.decompress((ROOT/'tooluse022/apk_archive'/p['compressed']).read_bytes())]
        h=hashlib.sha256();n=0
        for raw in chunks:h.update(raw);n+=len(raw);yield raw
        assert n==p['bytes'] and h.hexdigest()==p['sha256']
def segment_blocks(s,manifest_path):
    if s['kind']=='parent_pack':yield from pack_blocks()
    elif s['kind']=='patch':
        m=read(s['manifest']);base=(ROOT/s['manifest']).parent
        for p in m['parts']:
            raw=(base/p['path']).read_bytes();assert len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256'];yield raw
    else:
        path=s['path'];path=path if path.startswith('android_') else (Path(manifest_path).parent/path).as_posix()
        packed=(ROOT/path).read_bytes();assert hashlib.sha256(packed).hexdigest()==s['compressed_sha256'];yield zlib.decompress(packed)
def restore(manifest_path,out):
    assert not out.exists();m=read(manifest_path);h=hashlib.sha256();n=0;temp=out.with_suffix('.restoring');assert not temp.exists()
    with temp.open('xb') as f:
        for s in m['segments']:
            sh=hashlib.sha256();size=0
            for raw in segment_blocks(s,manifest_path):f.write(raw);h.update(raw);sh.update(raw);size+=len(raw);n+=len(raw)
            assert size==s['bytes'] and sh.hexdigest()==s['sha256']
    assert n==m['bytes'] and h.hexdigest()==m['sha256'];temp.rename(out);print(json.dumps({'restored':str(out),'bytes':n,'sha256':h.hexdigest()}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--download-upstream',action='store_true');p.add_argument('--manifest');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.download_upstream:download_upstream()
    if a.manifest:assert a.out;restore(a.manifest,a.out)
