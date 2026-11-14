"""Preserve the exact signed APK without duplicating its two large assets."""
import hashlib,json,struct,zipfile,zlib
from pathlib import Path
H=Path(__file__).resolve().parent
def main():
    m=json.loads((H/'reports/apk_manifest.json').read_text());path=Path(m['path']);dest=H/'apk_archive';dest.mkdir(exist_ok=True)
    def locator(z,name):
        info=z.getinfo(name);assert info.compress_type==zipfile.ZIP_STORED
        with path.open('rb') as f:
            f.seek(info.header_offset);head=f.read(30);assert head[:4]==b'PK\x03\x04'
        return info.header_offset+30+sum(struct.unpack_from('<HH',head,26)),info.file_size
    with zipfile.ZipFile(path) as z:p,pl=locator(z,'assets/epoch02.lspatch');b,bl=locator(z,'assets/model.lsp')
    assert 0<p<p+pl<=b<b+bl<=path.stat().st_size
    segments=[]
    def compress(name,start,size):
        out=dest/name;assert not out.exists();h=hashlib.sha256();packer=zlib.compressobj(6)
        with path.open('rb') as src,out.open('xb') as dst:
            src.seek(start);left=size
            while left:
                raw=src.read(min(left,1024*1024));assert raw;left-=len(raw);h.update(raw);dst.write(packer.compress(raw))
            dst.write(packer.flush())
        segments.append({'kind':'zlib','path':name,'bytes':size,'sha256':h.hexdigest(),'compressed_bytes':out.stat().st_size,'compressed_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    compress('prefix.zlib.bin',0,p)
    patch=json.loads((H/'patch_archive/manifest.json').read_text());assert patch['bytes']==pl
    segments.append({'kind':'patch','manifest':'android_epochs030/patch_archive/manifest.json','bytes':pl,'sha256':patch['sha256']})
    compress('bridge.zlib.bin',p+pl,b-p-pl)
    segments.append({'kind':'parent_pack','manifest':'tooluse022/apk_archive/manifest.json','bytes':bl,'sha256':m['parent_pack_sha256']})
    compress('suffix.zlib.bin',b+bl,path.stat().st_size-b-bl)
    record={'format':'exact-signed-apk-segments-v1','apk_name':path.name,'bytes':m['bytes'],'sha256':m['sha256'],'segments':segments,'public_download':json.loads((H/'reports/gofile_delivery.json').read_text())['url']}
    (dest/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'segments':len(segments),'small_archive_bytes':sum(s.get('compressed_bytes',0) for s in segments),'patch_bytes_already_preserved':pl}),flush=True)
if __name__=='__main__':main()
