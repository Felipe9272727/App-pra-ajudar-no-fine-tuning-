"""Build separate same-signed test instrumentation, never the production APK."""
from build import *
def main():
 src=H/'smoke';out=OUT/'smoke';out.mkdir(exist_ok=True);classes=out/'classes';classes.mkdir(exist_ok=True);dex=out/'dex';dex.mkdir(exist_ok=True)
 run(BT/'aapt2','link','-o',out/'resources.apk','--manifest',src/'AndroidManifest.xml','-I',JAR)
 run('java','com.sun.tools.javac.Main','-source','8','-target','8','-classpath',JAR,'-d',classes,*src.glob('src/**/*.java'))
 run('java','-cp',BT/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',JAR,'--output',dex,*classes.rglob('*.class'))
 unsigned=out/'unsigned.apk';final=out/'smoke.apk'
 with zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED) as z:
  with zipfile.ZipFile(out/'resources.apk') as res:
   for i in sorted(res.infolist(),key=lambda i:(i.filename!='AndroidManifest.xml',i.filename)):
    raw=res.read(i);kind=zipfile.ZIP_STORED if i.filename=='resources.arsc' else zipfile.ZIP_DEFLATED;z.writestr(aligned_info(z,i.filename,len(raw),kind),raw)
  z.write(dex/'classes.dex','classes.dex')
 run(BT/'zipalign','-c','4',unsigned)
 run('java','-jar',BT/'lib/apksigner.jar','sign','--ks','/tmp/liquid-fast020-signing/preview.p12','--ks-key-alias','liquid-sense-fast','--ks-pass','file:/tmp/liquid-fast020-signing/password','--min-sdk-version','28','--out',final,unsigned)
 run('java','-jar',BT/'lib/apksigner.jar','verify',final)
 print(json.dumps({'test_only_APK':str(final),'bytes':final.stat().st_size,'sha256':hashlib.sha256(final.read_bytes()).hexdigest()}))
if __name__=='__main__':main()
