"""Prepare UI, invoke exact source export once, sign verified payload in place."""
import pathlib,json,subprocess,zipfile,shutil,os,struct,hashlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=ROOT/'android_models021';OUT=pathlib.Path('/dev/shm/liquid-android/models021-apk');TOOLS=pathlib.Path('/dev/shm/liquid-android/tooling/android');BT=TOOLS/'build-tools';JAR=TOOLS/'platform/android.jar';SOURCE=HERE/'android';ENV={**os.environ,'LD_LIBRARY_PATH':str(BT/'lib64'),'JAVA_TOOL_OPTIONS':'-Xmx384m'}
def run(args,**kw):subprocess.run([str(a) for a in args],check=True,**kw)
def aligned_info(z,name,size,kind):
 x=zipfile.ZipInfo(name,date_time=(2026,11,12,0,0,0));x.compress_type=kind;x.file_size=size;offset=z.fp.tell()+30+len(name.encode())
 if kind==zipfile.ZIP_STORED and offset%4:
  pad=(-(offset+4))%4;x.extra=struct.pack('<HH',0xFFFF,pad)+bytes(pad)
 return x
def digest(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 OUT.mkdir(exist_ok=True);tmp=OUT/'intermediate';tmp.mkdir(exist_ok=True);unsigned=OUT/'unsigned.apk';final=OUT/'LiquidSense-0.2.0-specialist-preview.apk';assert not final.exists() and (not unsigned.exists() or '--resume-export' in sys.argv or '--resume-sign' in sys.argv),'Inspect partial state, never blind rebuild'
 lib=pathlib.Path('/dev/shm/liquid-android/prebuilt/models021/libliquid_sense.so');assert lib.exists()
 if '--resume-export' not in sys.argv and '--resume-sign' not in sys.argv:
  run([BT/'aapt2','compile','--dir',SOURCE/'res','-o',tmp/'resources.zip'],env=ENV);gen=tmp/'generated';gen.mkdir(exist_ok=True)
  run([BT/'aapt2','link','-o',tmp/'resources.apk','--manifest',SOURCE/'AndroidManifest.xml','-I',JAR,'-R',tmp/'resources.zip','--java',gen,'--custom-package','dev.liquidsense.chat','--auto-add-overlay'],env=ENV)
  classes=tmp/'classes';classes.mkdir(exist_ok=True);run(['java','com.sun.tools.javac.Main','-source','8','-target','8','-classpath',JAR,'-d',classes,*list((SOURCE/'src').rglob('*.java')),*gen.rglob('*.java')],env=ENV);dex=tmp/'dex';dex.mkdir(exist_ok=True);run(['java','-cp',BT/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',JAR,'--output',dex,*classes.rglob('*.class')],env=ENV)
  with zipfile.ZipFile(unsigned,'w',allowZip64=False) as z:
   with zipfile.ZipFile(tmp/'resources.apk') as resources:
    for info in resources.infolist():
     data=resources.read(info);z.writestr(aligned_info(z,info.filename,len(data),info.compress_type),data)
   for d in dex.glob('*.dex'):z.writestr(aligned_info(z,d.name,d.stat().st_size,zipfile.ZIP_DEFLATED),d.read_bytes())
   z.writestr(aligned_info(z,'lib/arm64-v8a/libliquid_sense.so',lib.stat().st_size,zipfile.ZIP_DEFLATED),lib.read_bytes())
   with zipfile.ZipFile('/dev/shm/liquid-android/apk/LiquidSense-0.1.0-preview.apk') as base:
    for info in base.infolist():
     if not info.filename.startswith('assets/') or info.filename=='assets/model.lsp':continue
     with base.open(info) as src,z.open(aligned_info(z,info.filename,info.file_size,info.compress_type),'w') as dst:shutil.copyfileobj(src,dst,1024*1024)
 # Credentials intentionally absent from the model-export process.
 clean={'PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin:/usr/bin:/bin','HOME':'/tmp','PYTHONPATH':'/home/agent/.local/lib/python3.12/site-packages','LS_CPU_THREADS':'4','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','HF_HUB_OFFLINE':'1'}
 if '--resume-sign' not in sys.argv:
  with zipfile.ZipFile(unsigned) as check:assert 'assets/model.lsp' not in check.namelist()
  with (HERE/'reports/export.log').open('x') as log:run(['python',HERE/'tools/export_into_apk.py',unsigned],env=clean,stdout=log,stderr=subprocess.STDOUT)
 # Payload is already4-byte aligned. No second multi-GB ZIP is created.
 run([BT/'zipalign','-c','-P','16','4',unsigned],env=ENV)
 with unsigned.open('rb') as f:f.seek(-min(65557,unsigned.stat().st_size),2);tail=f.read();end=tail.rfind(b'PK\x05\x06');assert end>=0;boundary=struct.unpack_from('<I',tail,end+16)[0]
 signclasses=tmp/'signclasses';signclasses.mkdir(exist_ok=True);jar=BT/'lib/apksigner.jar';run(['java','com.sun.tools.javac.Main','-classpath',jar,'-d',signclasses,HERE/'tools/TailSigner.java'],env=ENV)
 run(['java','-cp',str(signclasses)+':'+str(jar),'TailSigner',unsigned,str(boundary),'/tmp/liquid-fast020-signing/preview.p12','/tmp/liquid-fast020-signing/password'],env=ENV)
 unsigned.rename(final)
 for name,args in [('signature.txt',['java','-jar',jar,'verify','--verbose','--print-certs',final]),('badging.txt',[BT/'aapt2','dump','badging',final]),('permissions.txt',[BT/'aapt2','dump','permissions',final])]:
  r=subprocess.run([str(x) for x in args],check=True,capture_output=True,text=True,env=ENV);(HERE/'reports'/name).write_text(r.stdout)
 run([BT/'zipalign','-c','-P','16','4',final],env=ENV)
 source=json.loads((HERE/'reports/specialist_export.json').read_text());locator=json.loads((HERE/'reports/model_locator.json').read_text());locator['path']=str(final)
 with zipfile.ZipFile(final) as z:
  info=z.getinfo('assets/model.lsp');assert info.compress_type==zipfile.ZIP_STORED and info.file_size==source['pack_bytes']
  with z.open(info) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==source['pack_sha256']
  assert hashlib.sha256(z.read('lib/arm64-v8a/libliquid_sense.so')).hexdigest()==digest(lib)
 assert 'android.permission.INTERNET' not in (HERE/'reports/permissions.txt').read_text();assert 'fcb504e5004b8e0be879b952d597248da3a731c481c1f24cd1ac01502df5ac5b' in (HERE/'reports/signature.txt').read_text()
 (HERE/'reports/model_locator.json').write_text(json.dumps(locator,indent=2)+'\n')
 report={'status':'signed_015E_APK_built','file':str(final),'bytes':final.stat().st_size,'sha256':digest(final),'package':'dev.liquidsense.chat.fast','versionCode':3,'versionName':'0.2.0-models-preview','default_model':'specialist015E','specialist_bundled':True,'general_source':'optional installed dev.liquidsense.chat public model assets','histories_isolated':True,'previous_base_history_migrated_without_deleting_legacy_key':True,'original_APKs_preserved':True,'same_signing_certificate_as_020':True,'model_pack_sha256':source['pack_sha256'],'all546_tensors_match_exact_E':True,'internet_permission':False,'phone_execution_verified':False,'new_training_updates':0}
 (HERE/'reports/apk_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
