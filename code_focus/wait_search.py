"""Wait for the existing finite search; do not change or duplicate it."""
import json,os,time,urllib.request
url='https://api.github.com/repos/Felipe9272727/App-pra-ajudar-no-fine-tuning-/actions/runs/41891071593'
end=time.monotonic()+230*60
while time.monotonic()<end:
 headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'liquid-sense-code-focus'}
 token=os.environ.get('GH_TOKEN')
 if token:headers['Authorization']='Bearer '+token
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as r:j=json.load(r)
 print('RSI100',j['status'],j.get('conclusion'),flush=True)
 if j['status']=='completed':
  if j['conclusion']!='success':raise RuntimeError('RSI100 needs recovery before importing its final model')
  break
 time.sleep(30)
else:raise RuntimeError('Search still active; focused experiment not started')
