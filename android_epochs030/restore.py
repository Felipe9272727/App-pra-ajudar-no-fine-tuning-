"""Restore an exact APK/patch from immutable public Git fragments; no training."""
import argparse,hashlib,json,re,sys,urllib.request,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tooluse022.archive_apks import model_parts
REPO='Felipe9272727/App-pra-ajudar-no-fine-tuning-'
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ref',required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--patch-only',action='store_true');a=ap.parse_args()
    assert re.fullmatch('[0-9a-f]{40}',a.ref),'Use immutable commit SHA';assert not a.out.exists(),'Refuse overwrites'
    cache=Path('/dev/shm/liquid-android/epochs030-restore-cache');cache.mkdir(parents=True,exist_ok=True)
    def fetch(path,sha=None):
        assert '..' not in Path(path).parts and not Path(path).is_absolute()
        local=ROOT/path
        if local.is_file() and (sha is None or digest(local)==sha):return local
        target=cache/path;target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists() or (sha is not None and digest(target)!=sha):
            tmp=target.with_suffix('.download');urllib.request.urlretrieve(f'https://raw.githubusercontent.com/{REPO}/{a.ref}/{path}',tmp)
            if sha:assert digest(tmp)==sha
            tmp.replace(target)
        return target
    patch=json.loads(fetch('android_epochs030/patch_archive/manifest.json').read_text())
    def patch_parts():
        h=hashlib.sha256()
        for part in patch['parts']:
            raw=fetch('android_epochs030/patch_archive/'+part['path'],part['sha256']).read_bytes();assert len(raw)==part['bytes'];h.update(raw);yield raw
        assert h.hexdigest()==patch['sha256']
    if a.patch_only:segments=[{'kind':'patch'}];expected=patch
    else:expected=json.loads(fetch('android_epochs030/apk_archive/manifest.json').read_text());segments=expected['segments']
    h=hashlib.sha256();n=0;a.out.parent.mkdir(parents=True,exist_ok=True);tmp=a.out.with_suffix('.restoring');assert not tmp.exists(),'Inspect uncertain restoration'
    with tmp.open('xb') as f:
        for segment in segments:
            if segment['kind']=='patch':blocks=patch_parts()
            elif segment['kind']=='parent_pack':blocks=model_parts(json.loads(fetch(segment['manifest']).read_text()))
            else:
                raw=zlib.decompress(fetch('android_epochs030/apk_archive/'+segment['path'],segment['compressed_sha256']).read_bytes())
                assert len(raw)==segment['bytes'] and hashlib.sha256(raw).hexdigest()==segment['sha256'];blocks=[raw]
            for raw in blocks:f.write(raw);h.update(raw);n+=len(raw)
    assert n==expected['bytes'] and h.hexdigest()==expected['sha256'];tmp.rename(a.out)
    print(json.dumps({'bytes':n,'sha256':h.hexdigest(),'restored':str(a.out)}))
if __name__=='__main__':main()
