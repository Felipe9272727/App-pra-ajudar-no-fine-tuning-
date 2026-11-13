"""Preserve signed024APK exactly before retiring its redundant shm build copy."""
import hashlib,json,struct,zlib,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tooluse022.archive_apks import model_parts
H=ROOT/'loop025';d=H/'prior_apk024';d.mkdir(exist_ok=True);m=json.loads((ROOT/'android_thinking024/reports/apk_manifest.json').read_text());p=Path(m['path']);assert p.exists();assert not (d/'manifest.json').exists()
with zipfile.ZipFile(p) as z:i=z.getinfo('assets/model.lsp');assert i.compress_type==0
with p.open('rb') as f:
 f.seek(i.header_offset);offset=i.header_offset+30+sum(struct.unpack_from('<HH',f.read(30),26));f.seek(0);prefix=f.read(offset);f.seek(offset+i.file_size);suffix=f.read()
(d/'prefix.zlib.bin').write_bytes(zlib.compress(prefix,9));(d/'suffix.zlib.bin').write_bytes(zlib.compress(suffix,9));parent=json.loads((ROOT/'tooluse022/apk_archive/manifest.json').read_text());h=hashlib.sha256();h.update(prefix)
for b in model_parts(parent):h.update(b)
h.update(suffix);assert h.hexdigest()==m['sha256']
with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==m['sha256']
manifest={'format':'exact-apk-prefix-parent-pack-suffix-v1','original_sha256':m['sha256'],'original_bytes':p.stat().st_size,'prefix_bytes':len(prefix),'suffix_bytes':len(suffix),'pack_bytes':i.file_size,'pack_sha256':parent['pack']['sha256'],'reconstructed_full_sha_verified_before_refresh':True,'original_public_download':'https://gofile.io/d/hmAohFD5','restore_command':'python tooluse023/restore_apk_fragments.py loop025/prior_apk024 NEW_OUTPUT.apk','retired_only_redundant_build_copy':str(p),'backing_sources_protected':parent.get('immutable_sources_do_not_remove',[])}
(d/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');p.unlink();print('SIGNED024_EXACT_ARCHIVE_VERIFIED',m['sha256'])
