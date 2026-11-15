"""Exact031 APK archive reuses immutable030 prefix/patch/base/bridge segments."""
import hashlib,json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));H=ROOT/'android_ui032'
from tooluse022.archive_apks import model_parts
def blocks(segment):
    if segment['kind']=='zlib':
        packed=(ROOT/segment['path']).read_bytes();assert hashlib.sha256(packed).hexdigest()==segment['compressed_sha256'];yield zlib.decompress(packed)
    elif segment['kind']=='patch':
        m=json.loads((ROOT/segment['manifest']).read_text());parent=ROOT/segment['manifest']
        for p in m['parts']:
            raw=(parent.parent/p['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==p['sha256'];yield raw
    else:yield from model_parts(json.loads((ROOT/segment['manifest']).read_text()))
def main():
    m=json.loads((H/'reports/apk_manifest.json').read_text());old=json.loads((ROOT/'android_ui031/apk_archive_061/manifest.json').read_text());dest=H/'apk_archive';dest.mkdir(exist_ok=True)
    segments=old['segments'][:-1]
    for s in segments:
        if s['kind']=='zlib':assert s['path'].startswith('android_')
    prefix_bytes=sum(s['bytes'] for s in segments);out=dest/'suffix.zlib.bin';assert not out.exists();sha=hashlib.sha256();size=0;c=zlib.compressobj(6)
    with Path(m['path']).open('rb') as f,out.open('xb') as target:
        f.seek(prefix_bytes)
        while raw:=f.read(1024*1024):sha.update(raw);size+=len(raw);target.write(c.compress(raw))
        target.write(c.flush())
    segments.append({'kind':'zlib','path':out.relative_to(ROOT).as_posix(),'bytes':size,'sha256':sha.hexdigest(),'compressed_bytes':out.stat().st_size,'compressed_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    h=hashlib.sha256();n=0
    for s in segments:
        sh=hashlib.sha256();count=0
        for raw in blocks(s):h.update(raw);sh.update(raw);count+=len(raw);n+=len(raw)
        assert count==s['bytes'] and sh.hexdigest()==s['sha256']
    assert n==m['bytes'] and h.hexdigest()==m['sha256']
    record={'format':'exact-signed-apk-segments-v2','name':Path(m['path']).name,'bytes':n,'sha256':h.hexdigest(),'segments':segments,'all_segments_and_full_reconstruction_verified':True,'previous_APK_exact_archive_retained':True}
    (dest/'manifest.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'status':'exact_APK_preserved','sha256':h.hexdigest(),'additional_archive_bytes':out.stat().st_size}),flush=True)
if __name__=='__main__':main()
