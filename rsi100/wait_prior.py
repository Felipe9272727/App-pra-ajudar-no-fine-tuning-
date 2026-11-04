"""Avoid overlapping the earlier four-worker evaluation with this search."""
import json,os,time,urllib.request
url='https://api.github.com/repos/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/41865344082'
end=time.monotonic()+90*60
while time.monotonic()<end:
 headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'liquid-sense-rsi100'}
 token=os.environ.get('GH_TOKEN')
 if token:headers['Authorization']='Bearer '+token
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as response:run=json.load(response)
 print('PRIOR_WORKFLOW',run['status'],run.get('conclusion'),flush=True)
 if run['status']=='completed':break
 time.sleep(30)
else:raise RuntimeError('Previous evaluation still active; stopped before spending the 100-round budget')
