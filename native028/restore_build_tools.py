"""Recover the verified unused build tools; refuses overwrites and path escapes."""
from pathlib import Path
import json,tarfile,os
from archive_build_cache import DEST,BASE,Reader,inventory,digest

def main():
    h=Path(__file__).resolve().parent
    assert not json.load(open(h/'runtime.json'))['model_process_active'],'Do not restore RAM build cache during model work'
    m=json.load(open(DEST/'manifest.json'))
    for name in m['source_roots']:assert not (BASE/name).exists(),'Refusing existing root: '+name
    for part in m['parts']:
        with (DEST/part['path']).open('rb') as f:assert digest(f)==part['sha256']
    expected={r['path']:r for r in m['inventory']};seen=set()
    with tarfile.open(fileobj=Reader(m['parts']),mode='r|xz') as tar:
        for member in tar:
            assert member.name in expected and member.name not in seen
            path=Path(member.name);assert not path.is_absolute() and '..' not in path.parts
            if member.issym():
                link=Path(member.linkname);assert not link.is_absolute()
                resolved=(BASE/path.parent/link).resolve();assert resolved.is_relative_to(BASE.resolve())
            assert member.isfile() or member.isdir() or member.issym()
            tar.extract(member,path=BASE,filter='data');seen.add(member.name)
    assert seen==set(expected)
    assert inventory()==m['inventory'],'Restored data differs'
    print('ALL7367_BUILD_ENTRIES_RESTORED_VERIFIED')
if __name__=='__main__':main()
