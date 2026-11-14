"""Verify the archived 0.4 APK stream and recover its small shared assets."""
import hashlib,json,sys,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tooluse022.archive_apks import model_parts
HERE=ROOT/'android_epochs030';OUT=Path('/dev/shm/liquid-android/epochs030');OUT.mkdir(parents=True,exist_ok=True)
old=ROOT/'loop025/prior_apk024';m=json.loads((old/'manifest.json').read_text());pack=json.loads((ROOT/'tooluse022/apk_archive/manifest.json').read_text())
prefix=zlib.decompress((old/'prefix.zlib.bin').read_bytes());suffix=zlib.decompress((old/'suffix.zlib.bin').read_bytes())
h=hashlib.sha256();h.update(prefix)
for b in model_parts(pack):h.update(b)
h.update(suffix);assert h.hexdigest()==m['original_sha256']
# A sparse temporary ZIP view has no model bytes: use only non-model entries.
# The archived original has already been verified by its complete stream above.
view=OUT/'shared-assets-sparse.zip';assert not view.exists()
with view.open('xb') as f:f.write(prefix);f.seek(len(prefix)+m['pack_bytes']);f.write(suffix)
assets=OUT/'shared_assets';assets.mkdir(exist_ok=True);records=[]
with zipfile.ZipFile(view) as z:
    for i in z.infolist():
        if not i.filename.startswith('assets/') or i.filename in ('assets/model.lsp','assets/build_config.json','assets/tools_prefix.txt','assets/MICROPYTHON_LICENSE.txt'):continue
        name=i.filename.removeprefix('assets/');assert '/' not in name and name not in ('','.','..')
        raw=z.read(i);(assets/name).write_bytes(raw);records.append({'name':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
view.unlink() # Only a sparse, temporary view; all original archives remain.
(HERE/'reports/shared_assets.json').write_text(json.dumps({'source_apk_sha256':h.hexdigest(),'full_archived_stream_verified':True,'assets':records},indent=2)+'\n')
print(json.dumps(records),flush=True)
