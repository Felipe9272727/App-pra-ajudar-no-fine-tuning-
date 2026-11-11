"""Lossless archives for observed teaching features; original .pt files retained."""
import hashlib,json,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    files=sorted((HERE/'states').glob('*.pt'));assert len(files)==120
    dest=HERE/'archives';dest.mkdir(exist_ok=True);archive=dest/'teaching_states.tar.xz'
    with tarfile.open(archive,'w:xz',preset=6) as tar:
        for p in files:tar.add(p,arcname='states/'+p.name)
    manifest={'format':'tar.xz','sha256':sha(archive),'archive_bytes':archive.stat().st_size,
              'members':{str(p.relative_to(HERE)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in files},'parts':[]}
    with archive.open('rb') as f:
        i=0
        while data:=f.read(8*1024*1024):
            p=dest/('teaching_states.part%03d.bin'%i);p.write_bytes(data)
            manifest['parts'].append({'path':str(p.relative_to(HERE)),'sha256':sha(p),'bytes':len(data)});i+=1
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='members'},indent=2))
if __name__=='__main__':main()
