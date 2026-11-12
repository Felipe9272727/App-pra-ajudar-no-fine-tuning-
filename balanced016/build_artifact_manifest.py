"""Inventory settled study artifacts, including ignored raw logs and weight parts."""
import hashlib,json,subprocess,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
HERE=ROOT/'balanced016'
EXCLUDED={'artifact_manifest.json','artifact_verification.json','publication_receipt.json'}
def hash_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    jobs=subprocess.run(['ps','-C','python','-o','args='],text=True,capture_output=True).stdout.splitlines()
    active=[j for j in jobs if re.search(r'balanced016/(?:train|screen|validate)\.py',j)]
    assert not active,('Model workers still active',active)
    paths=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'staging' not in p.parts and p.name not in EXCLUDED)
    paths+=[ROOT/'BALANCED_JOINT_REPORT.md']
    files=[]
    for p in paths:
        relative=str(p.relative_to(ROOT));files.append({'path':relative,'bytes':p.stat().st_size,'sha256':hash_file(p),'git_blob':subprocess.check_output(['git','hash-object',relative],cwd=ROOT,text=True).strip()})
    result={'files':files,'file_count':len(files),'total_bytes':sum(f['bytes'] for f in files),'excludes_self_and_publication_receipts':True,'all_training_and_evaluation_workers_must_have_finished':True}
    (HERE/'artifact_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'files':len(files),'bytes':result['total_bytes']}))
if __name__=='__main__':main()
