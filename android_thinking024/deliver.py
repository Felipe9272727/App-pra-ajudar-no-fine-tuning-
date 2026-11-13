"""Upload the verified signed APK, keep guest-account data outside repository."""
import hashlib,json,os,re,subprocess,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'android_thinking024';PRIVATE=Path('/tmp/liquid-gofile-thinking024-upload')
def main():
 os.umask(0o077);PRIVATE.mkdir(mode=0o700,exist_ok=True)
 manifest=json.loads((HERE/'reports/apk_manifest.json').read_text());apk=Path(manifest['path']);assert apk.stat().st_size==manifest['bytes'];h=hashlib.sha256();md5=hashlib.md5()
 with apk.open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b);md5.update(b)
 assert h.hexdigest()==manifest['sha256'];(PRIVATE/'local_integrity.json').write_text(json.dumps({'bytes':apk.stat().st_size,'sha256':h.hexdigest(),'md5':md5.hexdigest()}))
 response=PRIVATE/'upload_response.json'
 if response.exists():
  previous=json.loads(response.read_text());assert previous.get('status')=='ok','Inspect incomplete upload receipt before any retry'
 else:
  with urllib.request.urlopen('https://api.gofile.io/servers',timeout=30) as r:servers=json.load(r)
  assert servers['status']=='ok';server=servers['data']['servers'][0]['name'];assert re.fullmatch('[A-Za-z0-9-]+',server)
  with response.open('x') as out,(PRIVATE/'upload.log').open('x') as log:
   p=subprocess.run(['curl','--fail-with-body','--show-error','--connect-timeout','30','--max-time','1200','-F','file=@'+str(apk),'https://'+server+'.gofile.io/contents/uploadfile'],stdout=out,stderr=log)
  assert p.returncode==0,'Inspect private upload log/receipt before retry'
 m=json.loads(response.read_text());assert m['status']=='ok';d=m['data'];assert d['name']==apk.name and int(d['size'])==apk.stat().st_size and d['md5']==md5.hexdigest();url=d['downloadPage'];assert re.fullmatch(r'https://gofile.io/d/[A-Za-z0-9]+',url)
 with urllib.request.urlopen(url,timeout=30) as r:status=r.status;r.read(8192)
 assert status==200
 public={'status':'uploaded_metadata_verified_public_page_available','url':url,'name':apk.name,'bytes':apk.stat().st_size,'sha256_local_signed_APK':h.hexdigest(),'md5_local_and_remote':md5.hexdigest(),'public_page_HTTP':status,'full_remote_redownload_performed':False,'phone_execution_verified':False}
 (HERE/'reports/gofile_delivery.json').write_text(json.dumps(public,indent=2)+'\n');print(json.dumps(public),flush=True)
if __name__=='__main__':main()
