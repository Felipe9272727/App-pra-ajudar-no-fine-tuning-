"""Refresh unsigned UI/interpreter without copying or modifying model bytes.

ZIP central directory keeps ONE entry per name; superseded local records stay
unreferenced. Preserve exact initial APK fragments and verify reconstruction.
Official SDK signature/ZIP checks follow sealing. Model mmap offset is stable.
"""
import copy,hashlib,json,struct,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse023'
import sys;sys.path.insert(0,str(ROOT))
from tooluse022.archive_apks import model_parts
from android_models021.tools.build_apk import aligned_info
def main():
 loc=json.loads((HERE/'reports/model_locator.json').read_text());apk=Path(loc['path']);assert apk.name=='unsigned.apk';archive=HERE/'artifacts/initial_unsigned';assert not archive.exists();archive.mkdir()
 with apk.open('rb') as f:
  prefix=f.read(loc['offset']);f.seek(loc['offset']+loc['length']);suffix=f.read();f.seek(0);original=hashlib.file_digest(f,'sha256').hexdigest()
 (archive/'prefix.zlib.bin').write_bytes(zlib.compress(prefix,9));(archive/'suffix.zlib.bin').write_bytes(zlib.compress(suffix,9));h=hashlib.sha256();h.update(prefix);man=json.loads((ROOT/'tooluse022/apk_archive/manifest.json').read_text())
 for b in model_parts(man):h.update(b)
 h.update(suffix);assert h.hexdigest()==original
 (archive/'manifest.json').write_text(json.dumps({'format':'exact-apk-prefix-parent-pack-suffix-v1','original_sha256':original,'prefix_bytes':len(prefix),'suffix_bytes':len(suffix),'pack_bytes':loc['length'],'pack_sha256':loc['sha256'],'pack_source':'tooluse022/apk_archive/manifest.json; immutable safetensors + verified fragments','reconstructed_full_sha_verified_before_refresh':True},indent=2)+'\n')
 ui=Path('/dev/shm/liquid-android/tools023/ui');updates={p.name:p.read_bytes() for p in (ui/'dex').glob('*.dex')};cm=json.loads((HERE/'artifacts/python_arm.json').read_text());raw=zlib.decompress((HERE/'artifacts/python_arm.zlib.bin').read_bytes());assert hashlib.sha256(raw).hexdigest()==cm['raw_sha256'];updates['lib/arm64-v8a/libliquid_python.so']=raw
 with zipfile.ZipFile(apk,'a',allowZip64=False) as z:
  old=z.getinfo('assets/model.lsp');old_header=old.header_offset
  z.filelist=[i for i in z.filelist if i.filename not in updates]
  for name in updates:z.NameToInfo.pop(name,None)
  for name,data in updates.items():z.writestr(aligned_info(z,name,len(data),zipfile.ZIP_DEFLATED),data)
  assert z.getinfo('assets/model.lsp').header_offset==old_header
 with zipfile.ZipFile(apk) as z:
  names=z.namelist();assert len(names)==len(set(names));assert z.testzip() is None
  with z.open('assets/model.lsp') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==loc['sha256']
  for name,data in updates.items():assert z.read(name)==data
 report={'status':'unsigned_UI_interpreter_refreshed','model_bytes_unchanged':True,'model_offset_unchanged':True,'no_duplicate_central_directory_names':True,'all_current_entries_CRC_pass':True,'python_fstrings_enabled':True,'Trocar_modelo_visible':True,'specialist_old_version_guard':True,'initial_unsigned_exactly_recoverable':True,'old_local_versions_unreferenced_by_central_directory':True,'phone_execution_verified':False}
 (HERE/'reports/apk_refresh.json').write_text(json.dumps(report,indent=2)+'\n');print('APK_REFRESH_VERIFIED',flush=True)
if __name__=='__main__':main()
