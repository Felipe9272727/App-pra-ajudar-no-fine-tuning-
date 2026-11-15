"""Rebuild the signed031 APK with no training. Requires preserved parent files."""
import hashlib,json,sys
from pathlib import Path
from archive_apk import blocks,H
def main():
    out=Path(sys.argv[1]);assert not out.exists();tmp=out.with_suffix('.restoring');assert not tmp.exists()
    m=json.loads((H/('apk_archive/manifest.json' if '--0.6.0' in sys.argv else 'apk_archive_061/manifest.json')).read_text());h=hashlib.sha256();n=0
    with tmp.open('xb') as f:
        for s in m['segments']:
            for raw in blocks(s):f.write(raw);h.update(raw);n+=len(raw)
    assert n==m['bytes'] and h.hexdigest()==m['sha256'];tmp.rename(out);print('EXACT_APK_RESTORED',h.hexdigest())
if __name__=='__main__':main()
