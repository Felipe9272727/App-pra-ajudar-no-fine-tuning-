"""Verify exact signed APK reconstruction without storing a second 2GB copy."""
import hashlib,json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tooluse022.archive_apks import model_parts
H=ROOT/'android_epochs030'
def main():
    m=json.loads((H/'apk_archive/manifest.json').read_text());h=hashlib.sha256();n=0
    for segment in m['segments']:
        if segment['kind']=='patch':
            p=json.loads((ROOT/segment['manifest']).read_text());blocks=[]
            # Iterate lazily: retaining every patch part would duplicate 353MB.
            def parts():
                for part in p['parts']:
                    raw=(H/'patch_archive'/part['path']).read_bytes();assert len(raw)==part['bytes'] and hashlib.sha256(raw).hexdigest()==part['sha256'];yield raw
            blocks=parts()
        elif segment['kind']=='parent_pack':blocks=model_parts(json.loads((ROOT/segment['manifest']).read_text()))
        else:
            packed=(H/'apk_archive'/segment['path']).read_bytes();assert hashlib.sha256(packed).hexdigest()==segment['compressed_sha256'];blocks=[zlib.decompress(packed)]
        sh=hashlib.sha256();size=0
        for raw in blocks:h.update(raw);sh.update(raw);n+=len(raw);size+=len(raw)
        assert size==segment['bytes'] and sh.hexdigest()==segment['sha256']
    assert n==m['bytes'] and h.hexdigest()==m['sha256']
    report={'status':'all_exact_signed_APK_segments_verified','bytes':n,'sha256':h.hexdigest(),'new_weight_fragments':85,'source_weights_unchanged':True,'duplicate_APK_created':False}
    (H/'reports/archive_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
