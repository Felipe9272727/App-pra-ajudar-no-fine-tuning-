"""Build a separate fast APK, streaming exact assets from preserved signed0.1.0."""
import pathlib,subprocess,zipfile,shutil,os,json,secrets,hashlib,argparse
ROOT=pathlib.Path(__file__).resolve().parents[2]
def run(args,**kw):subprocess.run([str(a) for a in args],check=True,**kw)
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--library',type=pathlib.Path,required=True);ap.add_argument('--old-apk',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True);assert not (a.out/'LiquidSense-0.1.1-speed-preview.apk').exists()
 tools=pathlib.Path('/dev/shm/liquid-android/tooling/android');bt=tools/'build-tools';jar=tools/'platform/android.jar';src=ROOT/'android_fast020/android';tmp=a.out/'intermediate';tmp.mkdir(exist_ok=True);env={**os.environ,'LD_LIBRARY_PATH':str(bt/'lib64'),'JAVA_TOOL_OPTIONS':'-Xmx512m'}
 assert digest(a.old_apk)=='9e0d4d58e3730d67a02afbad0ef6d4f796147963b7fc8222643be0fabbcadebe'
 run([bt/'aapt2','compile','--dir',src/'res','-o',tmp/'resources.zip'],env=env);gen=tmp/'generated';gen.mkdir(exist_ok=True)
 run([bt/'aapt2','link','-o',tmp/'resources.apk','--manifest',src/'AndroidManifest.xml','-I',jar,'-R',tmp/'resources.zip','--java',gen,'--custom-package','dev.liquidsense.chat','--auto-add-overlay'],env=env)
 classes=tmp/'classes';classes.mkdir(exist_ok=True);run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-classpath',jar,'-d',classes,*list((src/'src').rglob('*.java')),*gen.rglob('*.java')],env=env);dex=tmp/'dex';dex.mkdir(exist_ok=True)
 run(['java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',jar,'--output',dex,*classes.rglob('*.class')],env=env)
 unsigned=tmp/'unsigned.apk';shutil.copyfile(tmp/'resources.apk',unsigned)
 with zipfile.ZipFile(a.old_apk) as old,zipfile.ZipFile(unsigned,'a',allowZip64=True) as z:
  for d in dex.glob('*.dex'):z.write(d,d.name,compress_type=zipfile.ZIP_DEFLATED)
  z.write(a.library,'lib/arm64-v8a/libliquid_sense.so',compress_type=zipfile.ZIP_DEFLATED)
  for n in old.namelist():
   if not n.startswith('assets/'):continue
   info=old.getinfo(n);entry=zipfile.ZipInfo(n,date_time=info.date_time);entry.compress_type=info.compress_type;entry.file_size=info.file_size
   with old.open(n) as source,z.open(entry,'w') as dest:shutil.copyfileobj(source,dest,8*1024*1024)
 aligned=tmp/'aligned.apk';run([bt/'zipalign','-P','16','-f','4',unsigned,aligned],env=env);unsigned.unlink()
 private=pathlib.Path('/tmp/liquid-fast020-signing');private.mkdir(mode=0o700,exist_ok=True);private.chmod(0o700);keystore=private/'preview.p12';pw=private/'password';
 if not pw.exists():pw.write_text(secrets.token_hex(32));pw.chmod(0o600)
 signenv={**env,'LS_APK_SIGNING_PASSWORD':pw.read_text().strip()}
 if not keystore.exists():
  run(['keytool','-genkeypair','-keystore',keystore,'-alias','liquid-sense-fast','-storetype','PKCS12','-storepass:env','LS_APK_SIGNING_PASSWORD','-keypass:env','LS_APK_SIGNING_PASSWORD','-dname','CN=Liquid Sense Fast Preview','-keyalg','RSA','-keysize','2048','-validity','3650'],env=signenv);keystore.chmod(0o600)
 apk=a.out/'LiquidSense-0.1.1-speed-preview.apk';run(['java','-jar',bt/'lib/apksigner.jar','sign','--ks',keystore,'--ks-key-alias','liquid-sense-fast','--ks-pass','env:LS_APK_SIGNING_PASSWORD','--min-sdk-version','28','--v4-signing-enabled','false','--out',apk,aligned],env=signenv);aligned.unlink()
 result=subprocess.run(['java','-jar',str(bt/'lib/apksigner.jar'),'verify','--verbose','--print-certs',str(apk)],check=True,capture_output=True,text=True,env=env);(a.out/'signature.txt').write_text(result.stdout)
 run([bt/'zipalign','-c','-P','16','4',apk],env=env)
 for kind in ['badging','permissions']:
  result=subprocess.run([str(bt/'aapt2'),'dump',kind,str(apk)],check=True,capture_output=True,text=True,env=env);(a.out/(kind+'.txt')).write_text(result.stdout)
 assets={}
 with zipfile.ZipFile(apk) as z,zipfile.ZipFile(a.old_apk) as old:
  assert z.getinfo('assets/model.lsp').compress_type==zipfile.ZIP_STORED
  for n in old.namelist():
   if not n.startswith('assets/'):continue
   with z.open(n) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
   with old.open(n) as f:prior=hashlib.file_digest(f,'sha256').hexdigest()
   assert h==prior;assets[n]={'sha256':h,'bytes':z.getinfo(n).file_size,'identical_to_preserved_apk':True}
  assert assets['assets/model.lsp']['sha256']=='6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288'
 assert 'android.permission.INTERNET' not in (a.out/'permissions.txt').read_text()
 report={'status':'signed_arm64_fast_preview','file':apk.name,'bytes':apk.stat().st_size,'sha256':digest(apk),'package':'dev.liquidsense.chat.fast','activity':'dev.liquidsense.chat.MainActivity','version':'0.1.1-speed-preview','abi':'arm64-v8a','minimum_android':9,'model':'unchanged general principal','source_checkpoint_sha256':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8','assets':assets,'native_library_sha256':digest(a.library),'original_apk_preserved':True,'original_installed_app_and_history_preserved_by_separate_package':True,'internet_permission':False,'android_device_execution_verified':False,'physical_phone_speed_measured':False,'signing_key':'private local key retained; never published'}
 (a.out/'apk_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['file','bytes','sha256','package','version']}))
if __name__=='__main__':main()
