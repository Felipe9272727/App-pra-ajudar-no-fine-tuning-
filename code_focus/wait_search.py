"""Wait for the checkpointed local continuation without inspecting test scores."""
import base64,json,os,time,urllib.request,urllib.parse,urllib.error
branch='codex/liquid-sense-local-cpu-20261104'
url='https://api.github.com/repos/Felipe9272727/App-pra-ajudar-no-fine-tuning-/contents/rsi100/status.json?ref='+urllib.parse.quote(branch,safe='')
end=time.monotonic()+230*60
while time.monotonic()<end:
 headers={'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'liquid-sense-code-focus'}
 token=os.environ.get('GH_TOKEN')
 if token:headers['Authorization']='Bearer '+token
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=30) as r:payload=json.load(r)
  j=json.loads(base64.b64decode(payload['content']))
 except urllib.error.HTTPError as exc:
  if exc.code not in (429,500,502,503,504):raise
  print('STATUS_READ_RETRY',exc.code,flush=True);time.sleep(30);continue
 print('LOCAL_RSI100',j['status'],j['rounds_completed'],flush=True)
 if j['status']=='complete' and j['rounds_completed']==100 and j['final_test_evaluated']:
  print('LOCAL_PARENT_COMPLETE; import frozen weights only',flush=True);break
 time.sleep(30)
else:raise RuntimeError('Local search not complete within waiting budget; no focused inference started')
