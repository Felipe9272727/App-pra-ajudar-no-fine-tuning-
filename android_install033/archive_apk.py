"""Preserve the clean signed APK, referencing unchanged base/patch payloads."""
import hashlib,json,struct,zipfile,zlib
from pathlib import Path
from portable_restore import segment_blocks
H=Path(__file__).resolve().parent;ROOT=H.parent
def main():
    m=json.loads((H/'reports/apk_manifest.json').read_text());apk=Path(m['path']);dest=H/'apk_archive';dest.mkdir(exist_ok=True);segments=[]
    with zipfile.ZipFile(apk) as z:
        large=[]
        for name,kind,manifest in [('assets/model.lsp','parent_pack','tooluse022/apk_archive/manifest.json'),('assets/epoch02.lspatch','patch','android_epochs030/patch_archive/manifest.json')]:
            i=z.getinfo(name);assert i.compress_type==0
            with apk.open('rb') as f:f.seek(i.header_offset+26);nl,el=struct.unpack('<HH',f.read(4))
            offset=i.header_offset+30+nl+el;large.append((offset,i.file_size,kind,manifest))
    position=0
    def compressed(start,size):
        out=dest/('part%02d.zlib.bin'%len(segments));assert not out.exists();h=hashlib.sha256();c=zlib.compressobj(6)
        with apk.open('rb') as f,out.open('xb') as dst:
            f.seek(start);left=size
            while left:
                raw=f.read(min(left,1024*1024));assert raw;left-=len(raw);h.update(raw);dst.write(c.compress(raw))
            dst.write(c.flush())
        segments.append({'kind':'zlib','path':out.relative_to(ROOT).as_posix(),'bytes':size,'sha256':h.hexdigest(),'compressed_bytes':out.stat().st_size,'compressed_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    for offset,size,kind,manifest in sorted(large):
        compressed(position,offset-position);expected=json.loads((ROOT/manifest).read_text());expected=expected['pack'] if kind=='parent_pack' else expected
        segments.append({'kind':kind,'manifest':manifest,'bytes':size,'sha256':expected['sha256']});position=offset+size
    compressed(position,apk.stat().st_size-position)
    h=hashlib.sha256();n=0
    for s in segments:
        for raw in segment_blocks(s,'android_install033/apk_archive/manifest.json'):h.update(raw);n+=len(raw)
    assert n==m['bytes'] and h.hexdigest()==m['sha256']
    (dest/'manifest.json').write_text(json.dumps({'format':'exact-signed-apk-segments-v2','name':apk.name,'bytes':n,'sha256':h.hexdigest(),'segments':segments,'full_reconstruction_verified':True},indent=2)+'\n');print('CLEAN_APK_ARCHIVE_VERIFIED',h.hexdigest())
if __name__=='__main__':main()
