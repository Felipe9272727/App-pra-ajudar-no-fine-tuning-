"""Restore exact archived engineering APK into a NEW output path."""
import hashlib,json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tooluse022.archive_apks import model_parts
def main():
 directory=Path(sys.argv[1]);out=Path(sys.argv[2]);assert not out.exists();m=json.loads((directory/'manifest.json').read_text());parent=json.loads((ROOT/'tooluse022/apk_archive/manifest.json').read_text());assert parent['pack']['sha256']==m['pack_sha256'];h=hashlib.sha256();tmp=out.with_suffix('.restoring')
 with tmp.open('xb') as f:
  def put(b):h.update(b);f.write(b)
  put(zlib.decompress((directory/'prefix.zlib.bin').read_bytes()))
  for b in model_parts(parent):put(b)
  put(zlib.decompress((directory/'suffix.zlib.bin').read_bytes()))
 assert h.hexdigest()==m['original_sha256'];tmp.rename(out);print('EXACT_APK_RESTORED',m['original_sha256'])
if __name__=='__main__':main()
