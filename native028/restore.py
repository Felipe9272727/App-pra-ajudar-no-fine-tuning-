"""Restore missing public archive parts at an explicit immutable Git commit."""
import argparse,hashlib,json,re,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
REPO='Felipe9272727/App-pra-ajudar-no-fine-tuning-'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def obtain(url,path,expected=None,expected_bytes=None):
    if path.exists():
        if expected:assert sha(path)==expected,'Existing file differs; never overwrite: '+str(path)
        if expected_bytes is not None:assert path.stat().st_size==expected_bytes
        return
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.download')
    assert not tmp.exists(),'Investigate incomplete download: '+str(tmp)
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'LiquidSense028-restore'}),timeout=60) as r,tmp.open('xb') as f:
        while block:=r.read(1024*1024):f.write(block)
    if expected:assert sha(tmp)==expected,'Downloaded hash mismatch'
    if expected_bytes is not None:assert tmp.stat().st_size==expected_bytes
    tmp.rename(path)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ref',required=True,help='Exact40hex repository commit containing the archives')
    ap.add_argument('--stage',nargs='+',choices=['initial_factors','recovery_step48','sft_epoch1','sft_final','policy_final'],default=[])
    ap.add_argument('--tokenizer',action='store_true');args=ap.parse_args();assert re.fullmatch('[0-9a-f]{40}',args.ref)
    for stage in args.stage:
        folder=H/'checkpoints'/stage;url='https://raw.githubusercontent.com/'+REPO+'/'+args.ref+'/native028/checkpoints/'+stage+'/'
        obtain(url+'manifest.json',folder/'manifest.json');m=json.loads((folder/'manifest.json').read_text());full=hashlib.sha256()
        assert m['parent_sha256']==json.loads((H/'config.json').read_text())['parent_sha256']
        for part in m['parts']:
            assert re.fullmatch(r'part\d{4}\.bin',part['path'])
            path=folder/part['path'];obtain(url+part['path'],path,part['sha256'],part['bytes'])
            with path.open('rb') as f:
                while block:=f.read(1024*1024):full.update(block)
        assert full.hexdigest()==m['compressed_sha256'];print('CHECKPOINT028_RESTORED_VERIFIED',stage)
    if args.tokenizer:
        for source in json.loads((H/'provisioning.json').read_text())['sources']:
            if source['path']=='upstream/tokenizer.json':obtain(source['url'],ROOT/source['path'],source['sha256'],source['bytes'])
        print('TOKENIZER028_VERIFIED')
    print('Base safetensors and immutable best.pt remain required from the existing project setup; this script does not replace them.')
if __name__=='__main__':main()
