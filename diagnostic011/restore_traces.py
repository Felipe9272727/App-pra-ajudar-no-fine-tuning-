"""Restore lossless tensor traces, validating archive/member SHA256 values."""
from pathlib import Path
import json,hashlib,tarfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def main():
 m=json.loads((HERE/'activation_archive.json').read_text());path=HERE/'activation_archive.tar.xz';h=hashlib.sha256()
 with path.open('wb') as f:
  for r in m['chunks']:
   data=(ROOT/r['path']).read_bytes();assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
   f.write(data);h.update(data)
 assert h.hexdigest()==m['archive_sha256']
 expected={r['path']:r for r in m['members']}
 with tarfile.open(path,'r:xz') as archive:
  assert set(archive.getnames())==set(expected)
  for member in archive:
   assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
   row=expected[member.name];data=archive.extractfile(member).read();assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
   dest=HERE/member.name;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.exists():assert hashlib.sha256(dest.read_bytes()).hexdigest()==row['sha256']
   else:dest.write_bytes(data)
 print('All eight observation artifacts verified and restored.')
if __name__=='__main__':main()
