"""Build/sign a real Android APK, with the Rust library and model inside its assets."""
import argparse,pathlib,subprocess,zipfile,shutil,os,json,secrets,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
def run(args,**kw):subprocess.run([str(a) for a in args],check=True,**kw)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--tools',type=pathlib.Path,required=True);ap.add_argument('--target',type=pathlib.Path,required=True);ap.add_argument('--model',type=pathlib.Path,required=True);ap.add_argument('--out',type=pathlib.Path,required=True);ap.add_argument('--precision',choices=['bf16','q8'],default='bf16');ap.add_argument('--prepare-only',action='store_true');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 source=ROOT/'android_chat/android';tmp=a.out/'intermediate';tmp.mkdir(exist_ok=True);bt=a.tools/'build-tools';jar=a.tools/'platform/android.jar';env={**os.environ,'LD_LIBRARY_PATH':str(bt/'lib64')}
 run([bt/'aapt2','compile','--dir',source/'res','-o',tmp/'resources.zip'],env=env)
 gen=tmp/'generated';gen.mkdir(exist_ok=True)
 run([bt/'aapt2','link','-o',tmp/'resources.apk','--manifest',source/'AndroidManifest.xml','-I',jar,'-R',tmp/'resources.zip','--java',gen,'--auto-add-overlay'],env=env)
 classes=tmp/'classes';classes.mkdir(exist_ok=True);java=list((source/'src').rglob('*.java'))+list(gen.rglob('*.java'))
 run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-bootclasspath',jar,'-d',classes,*java])
 dex=tmp/'dex';dex.mkdir(exist_ok=True)
 run(['java','-cp',bt/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',jar,'--output',dex,*classes.rglob('*.class')])
 if a.prepare_only:print('ANDROID_JAVA_DEX_READY');return
 unsigned=tmp/'unsigned.apk';shutil.copyfile(tmp/'resources.apk',unsigned)
 with zipfile.ZipFile(unsigned,'a',allowZip64=True) as z:
  for d in dex.glob('*.dex'):z.write(d,d.name,compress_type=zipfile.ZIP_DEFLATED)
  for target,abi in [('aarch64-linux-android','arm64-v8a'),('x86_64-linux-android','x86_64')]:
   library=a.target/target/'release/libliquid_sense.so'
   if library.exists():z.write(library,'lib/'+abi+'/libliquid_sense.so',compress_type=zipfile.ZIP_DEFLATED)
  z.write(a.model/(a.precision+'.lsp'),'assets/model.lsp',compress_type=zipfile.ZIP_STORED)
  z.write(a.model/'tokenizer.json','assets/tokenizer.json',compress_type=zipfile.ZIP_STORED)
  z.write(a.model/'identity.json','assets/identity.json',compress_type=zipfile.ZIP_DEFLATED)
  z.write(ROOT/'upstream/LICENSE','assets/LICENSE_QWEN.txt',compress_type=zipfile.ZIP_DEFLATED)
  z.write(ROOT/'android_chat/NOTICE.txt','assets/NOTICE.txt',compress_type=zipfile.ZIP_DEFLATED)
 aligned=tmp/'aligned.apk';run([bt/'zipalign','-P','16','-f','4',unsigned,aligned],env=env);unsigned.unlink()
 keystore=a.out/'preview-signing.p12';password=secrets.token_hex(24);signenv={**env,'LS_APK_SIGNING_PASSWORD':password}
 run(['keytool','-genkeypair','-keystore',keystore,'-alias','liquid-sense-preview','-storetype','PKCS12','-storepass:env','LS_APK_SIGNING_PASSWORD','-keypass:env','LS_APK_SIGNING_PASSWORD','-dname','CN=Liquid Sense Preview','-keyalg','RSA','-keysize','2048','-validity','3650'],env=signenv)
 apk=a.out/'LiquidSense-0.1.0-preview.apk'
 run(['java','-jar',bt/'lib/apksigner.jar','sign','--ks',keystore,'--ks-key-alias','liquid-sense-preview','--ks-pass','env:LS_APK_SIGNING_PASSWORD','--min-sdk-version','28','--v4-signing-enabled','false','--out',apk,aligned],env=signenv);aligned.unlink();keystore.unlink()
 p=subprocess.run(['java','-jar',str(bt/'lib/apksigner.jar'),'verify','--verbose','--print-certs',str(apk)],check=True,text=True,capture_output=True);(a.out/'signature.txt').write_text(p.stdout)
 run([bt/'zipalign','-c','-P','16','4',apk],env=env)
 with zipfile.ZipFile(apk) as z:
  model=z.getinfo('assets/model.lsp');assert model.compress_type==zipfile.ZIP_STORED and model.file_size==(a.model/(a.precision+'.lsp')).stat().st_size
  assert z.getinfo('assets/tokenizer.json').compress_type==zipfile.ZIP_STORED
  assert 'lib/arm64-v8a/libliquid_sense.so' in z.namelist()
 h=hashlib.sha256()
 with apk.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 report={'status':'signed_apk_built','file':apk.name,'bytes':apk.stat().st_size,'sha256':h.hexdigest(),'model_bundled':True,'model_bytes':model.file_size,'model_pack_sha256':json.loads((a.model/(a.precision+'_export.json')).read_text())['sha256'],'source_checkpoint_sha256':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8','minimum_android':9,'abi':'arm64-v8a','precision':a.precision,'internet_permission':False,'signing':'Fresh preview certificate; rebuilds can require reinstall. Signing key is not included or published.','android_device_execution_verified':False}
 (a.out/'apk_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
