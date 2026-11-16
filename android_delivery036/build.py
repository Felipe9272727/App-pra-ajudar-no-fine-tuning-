"""Build tiny independent native Android diagnosis/installer; no model assets."""
from pathlib import Path
import json,os,sys,zipfile,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));H=ROOT/'android_delivery036';SRC=H/'android';OUT=Path('/dev/shm/liquid036');SDK=Path('/dev/shm/liquid-android/tooling/android');BT=SDK/'build-tools';JAR=SDK/'platform/android.jar';ENV={**os.environ,'JAVA_TOOL_OPTIONS':'-Xmx384m','LD_LIBRARY_PATH':str(BT/'lib64')}
from android_models021.tools.build_apk import aligned_info
def run(*args):return subprocess.run([str(v) for v in args],check=True,env=ENV,capture_output=True,text=True)
def main():
 OUT.mkdir(exist_ok=True);gen=OUT/'gen';gen.mkdir(exist_ok=True);classes=OUT/'classes';classes.mkdir(exist_ok=True);dex=OUT/'dex';dex.mkdir(exist_ok=True)
 logs=[]
 for args in [(BT/'aapt2','compile','--dir',SRC/'res','-o',OUT/'resources.zip'),(BT/'aapt2','link','-o',OUT/'resources.apk','--manifest',SRC/'AndroidManifest.xml','-I',JAR,'-R',OUT/'resources.zip','--java',gen,'--custom-package','dev.liquidsense.installcheck','--auto-add-overlay'),('java','com.sun.tools.javac.Main','-source','8','-target','8','-classpath',JAR,'-d',classes,*SRC.glob('src/**/*.java'),*gen.rglob('*.java'))]:
  r=run(*args);logs.append(r.stdout+r.stderr)
 r=run('java','-cp',BT/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',JAR,'--output',dex,*classes.rglob('*.class'));logs.append(r.stdout+r.stderr)
 (H/'reports/build.log').write_text('\n'.join(logs))
 unsigned=OUT/'unsigned.apk';final=OUT/'LiquidSense-Reparador-0.2.apk'
 with zipfile.ZipFile(unsigned,'w') as z:
  with zipfile.ZipFile(OUT/'resources.apk') as res:
   for i in sorted(res.infolist(),key=lambda i:(i.filename!='AndroidManifest.xml',i.filename)):
    raw=res.read(i);kind=0 if i.filename=='resources.arsc' else i.compress_type;z.writestr(aligned_info(z,i.filename,len(raw),kind),raw)
  z.writestr('assets/integrity.json',(SRC/'assets/integrity.json').read_bytes(),compress_type=zipfile.ZIP_DEFLATED);raw=(dex/'classes.dex').read_bytes();z.writestr(aligned_info(z,'classes.dex',len(raw),8),raw)
 run(BT/'zipalign','-c','4',unsigned)
 run('java','-jar',BT/'lib/apksigner.jar','sign','--ks','/tmp/liquid-fast020-signing/preview.p12','--ks-key-alias','liquid-sense-fast','--ks-pass','file:/tmp/liquid-fast020-signing/password','--min-sdk-version','28','--v1-signing-enabled','true','--v2-signing-enabled','true','--v3-signing-enabled','true','--out',final,unsigned)
 r=run('java','-jar',BT/'lib/apksigner.jar','verify','--verbose','--print-certs',final);(H/'reports/signature.txt').write_text(r.stdout);assert 'fcb504e5004b8e0be879b952d597248da3a731c481c1f24cd1ac01502df5ac5b'in r.stdout
 r=run(BT/'aapt2','dump','permissions',final);(H/'reports/permissions.txt').write_text(r.stdout);assert 'android.permission.INTERNET' in r.stdout
 run(BT/'zipalign','-c','4',final)
 with zipfile.ZipFile(final) as z:assert z.testzip() is None
 m={'status':'signed_native_diagnostic_APK_built','path':str(final),'bytes':final.stat().st_size,'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'package':'dev.liquidsense.installcheck','versionCode':2,'no_model_assets':True,'INTERNET_permission':True,'reads_only_user_chosen_ZIP':True,'phone_execution_verified':False};(H/'reports/apk_manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(m))
if __name__=='__main__':main()
