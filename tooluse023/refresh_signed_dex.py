"""Preserve exact pre-doc-lookup signed build, replace only central-dir DEX refs."""
import hashlib,json,struct,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse023'
import sys;sys.path.insert(0,str(ROOT))
from tooluse022.archive_apks import model_parts
from android_models021.tools.build_apk import aligned_info
def main():
 loc=json.loads((HERE/'reports/model_locator.json').read_text());apk=Path(loc['path']);assert apk.name=='LiquidSense-0.3.0-tools-preview.apk';old=json.loads((HERE/'reports/apk_manifest.json').read_text());archive=HERE/'artifacts/signed_before_official_docs';assert not archive.exists();archive.mkdir()
 with apk.open('rb') as f:
  prefix=f.read(loc['offset']);f.seek(loc['offset']+loc['length']);suffix=f.read();f.seek(0);h=hashlib.file_digest(f,'sha256').hexdigest();assert h==old['sha256']
 (archive/'prefix.zlib.bin').write_bytes(zlib.compress(prefix,9));(archive/'suffix.zlib.bin').write_bytes(zlib.compress(suffix,9));whole=hashlib.sha256();whole.update(prefix);man=json.loads((ROOT/'tooluse022/apk_archive/manifest.json').read_text())
 for b in model_parts(man):whole.update(b)
 whole.update(suffix);assert whole.hexdigest()==h
 metadata={'format':'exact-apk-prefix-parent-pack-suffix-v1','original_sha256':h,'prefix_bytes':len(prefix),'suffix_bytes':len(suffix),'pack_bytes':loc['length'],'pack_sha256':loc['sha256'],'pack_source':'tooluse022/apk_archive/manifest.json','reconstructed_full_sha_verified_before_refresh':True};(archive/'manifest.json').write_text(json.dumps(metadata,indent=2)+'\n');(HERE/'reports/apk_manifest_before_official_docs.json').write_text(json.dumps(old,indent=2)+'\n')
 updates={p.name:p.read_bytes() for p in Path('/dev/shm/liquid-android/tools023/ui/dex').glob('*.dex')}
 with zipfile.ZipFile(apk,'a',allowZip64=False) as z:
  z.filelist=[i for i in z.filelist if i.filename not in updates]
  for name in updates:z.NameToInfo.pop(name,None)
  for name,data in updates.items():z.writestr(aligned_info(z,name,len(data),zipfile.ZIP_DEFLATED),data)
 with zipfile.ZipFile(apk) as z:
  assert len(z.namelist())==len(set(z.namelist()));assert z.testzip() is None
  with z.open('assets/model.lsp') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==loc['sha256']
 unsigned=apk.with_name('unsigned.apk');assert not unsigned.exists();apk.rename(unsigned);loc['path']=str(unsigned);(HERE/'reports/model_locator.json').write_text(json.dumps(loc,indent=2)+'\n');print('DEX_REFRESH_PARENT_UNCHANGED_READY_TO_RESIGN',flush=True)
if __name__=='__main__':main()
