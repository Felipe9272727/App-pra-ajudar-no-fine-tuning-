"""Pause each decision until the assistant confirms its durable GitHub commit.

No GitHub credentials are stored in the model process. The companion coordinator
uses the connected GitHub tools and acknowledges only a verified branch head.
"""
import hashlib,json,os,subprocess,time,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'local_cpu'

def atomic(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)

def allowed(path):
    import re
    return path=='RSI100_REPORT.md' or bool(re.fullmatch(r'rsi100/(?:status|progress|calibration_\d{3}|best_metrics|baseline_metrics|frozen|summary|validation_[a-z0-9_]+|final_[a-z0-9_]+|round_\d{3})\.json',path)) or bool(re.fullmatch(r'rsi100/checkpoints/(?:baseline|best|accepted_\d{3})\.pt',path))

def publish(phase):
    source=os.environ['LS_SOURCE_COMMIT'];session=os.environ['LS_LOCAL_SESSION']
    def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,timeout=30).strip()
    git('merge-base','--is-ancestor',source,'HEAD')
    assert all(allowed(p) for p in git('diff','--name-only',source,'HEAD').splitlines()),'Concurrent source edit'
    publication_id=str(uuid.uuid4())
    atomic(ROOT/'rsi100/progress.json',{'run_id':session,'source_commit':source,'phase':phase,'publication_id':publication_id,
      'execution':'local CPU; publication controlled by assistant','last_observed_unix':time.time()})
    paths=set(git('diff','--name-only','HEAD').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    paths=sorted(p for p in paths if allowed(p))
    request={'id':publication_id,'session':session,'phase':phase,'parent':git('rev-parse','HEAD'),
      'files':[{'path':p,'size':(ROOT/p).stat().st_size,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),
                'git_blob':git('hash-object',p)} for p in paths],'created_unix':time.time()}
    atomic(HERE/'pending_publish.json',request)
    print('LOCAL_PUBLISH_PENDING',json.dumps({'id':request['id'],'phase':phase,'files':len(paths)}),flush=True)
    end=time.monotonic()+540
    while time.monotonic()<end:
        try:ack=json.loads((HERE/'publish_ack.json').read_text())
        except (FileNotFoundError,json.JSONDecodeError):ack={}
        if ack.get('id')==request['id']:
            if not ack.get('verified'):raise RuntimeError('Remote publication not verified')
            assert git('rev-parse','HEAD')==ack['commit'],'Local publication head does not match acknowledgment'
            print('LOCAL_SAVED',phase,ack['commit'],flush=True)
            return
        time.sleep(.5)
    raise TimeoutError('No durable publication acknowledgment; do not continue search')
