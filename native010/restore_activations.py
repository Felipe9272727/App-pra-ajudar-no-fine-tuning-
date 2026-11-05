"""Restore the archived construction observations; verifies all bytes first."""
from pathlib import Path
import json,hashlib,zipfile
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'activation_archive.json').read_text())
archive=HERE/'activation_archive.zip'
h=hashlib.sha256()
with archive.open('wb') as out:
 for row in manifest['chunks']:
  data=(HERE.parent/row['path']).read_bytes()
  assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
  h.update(data);out.write(data)
assert h.hexdigest()==manifest['archive_sha256']
with zipfile.ZipFile(archive) as z:
 assert set(z.namelist())==set(manifest['members'])
 for name,row in manifest['members'].items():
  assert Path(name).name==name
  data=z.read(name);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
  path=HERE/name
  if path.exists():assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
  else:path.write_bytes(data)
print('All calibration observations restored and verified.')
