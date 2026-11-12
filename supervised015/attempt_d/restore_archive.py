"""Reconstruct a chunked training cache or optimizer archive without overwrite."""
import argparse,hashlib,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    assert not a.output.exists();m=json.loads((a.directory/'manifest.json').read_text());assert m['format']=='torch-zip-parts-v1';whole=hashlib.sha256();size=0
    with a.output.open('xb') as out:
        for part in m['parts']:
            b=(a.directory/part['path']).read_bytes();assert len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256'];out.write(b);whole.update(b);size+=len(b)
    assert size==m['bytes'] and whole.hexdigest()==m['stream_sha256'];print(whole.hexdigest())
if __name__=='__main__':main()
