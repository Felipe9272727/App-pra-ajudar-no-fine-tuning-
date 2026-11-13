"""Stream exact preserved general pack into the Tools0.4 update; sign later.

prepare: UI, native libraries, shared assets and verified parent model only.
seal: attach eligible weights/config, sign, verify; never auto-promote a failure.
"""
import argparse,hashlib,json,os,shutil,struct,subprocess,sys,zipfile,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));HERE=ROOT/'android_thinking024';OUT=Path('/dev/shm/liquid-android/thinking024-apk');SDK=Path('/dev/shm/liquid-android/tooling/android');BT=SDK/'build-tools';ENV={**os.environ,'LD_LIBRARY_PATH':str(BT/'lib64'),'JAVA_TOOL_OPTIONS':'-Xmx384m'}
from tooluse022.archive_apks import model_parts
from android_models021.tools.build_apk import aligned_info
PACK_SHA='6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288'
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(*args):subprocess.run([str(a) for a in args],check=True,env=ENV)
def prepare():
 OUT.mkdir(exist_ok=True);unsigned=OUT/'unsigned.apk';assert not unsigned.exists(),'Inspect/resume existing preparation, never duplicate model';ui=Path('/dev/shm/liquid-android/thinking024/ui');lib=Path('/dev/shm/liquid-android/prebuilt/thinking024/libliquid_sense.so');assert lib.exists() and (ui/'resources.apk').exists()
 free=os.statvfs('/dev/shm');assert free.f_bavail*free.f_frsize>1620*1024*1024,'Finish compiler/cache cleanup before streaming APK'
 man=json.loads((ROOT/'tooluse022/apk_archive/manifest.json').read_text());assert man['pack']['sha256']==PACK_SHA
 with zipfile.ZipFile(unsigned,'w',allowZip64=False) as z:
  def add(name,data,kind=zipfile.ZIP_DEFLATED):z.writestr(aligned_info(z,name,len(data),kind),data)
  with zipfile.ZipFile(ui/'resources.apk') as res:
   for i in res.infolist():add(i.filename,res.read(i),i.compress_type)
  for dex in (ui/'dex').glob('*.dex'):add(dex.name,dex.read_bytes())
  add('lib/arm64-v8a/libliquid_sense.so',lib.read_bytes())
  py=json.loads((ROOT/'tooluse023/artifacts/python_arm.json').read_text());raw=zlib.decompress((ROOT/'tooluse023/artifacts/python_arm.zlib.bin').read_bytes());assert hashlib.sha256(raw).hexdigest()==py['raw_sha256'];add('lib/arm64-v8a/libliquid_python.so',raw)
  with zipfile.ZipFile('/dev/shm/liquid-android/models021-apk/LiquidSense-0.2.0-specialist-preview.apk') as source:
   for i in source.infolist():
    if not i.filename.startswith('assets/') or i.filename=='assets/model.lsp':continue
    with source.open(i) as src,z.open(aligned_info(z,i.filename,i.file_size,i.compress_type),'w') as dest:shutil.copyfileobj(src,dest,1024*1024)
  add('assets/tools_prefix.txt',(ROOT/'tooluse022/tools_prefix.txt').read_bytes(),zipfile.ZIP_STORED);add('assets/MICROPYTHON_LICENSE.txt',(ROOT/'tooluse022/python_port/MICROPYTHON_LICENSE.txt').read_bytes())
  info=aligned_info(z,'assets/model.lsp',man['pack']['bytes'],zipfile.ZIP_STORED);offset=z.fp.tell()+30+len(info.filename.encode())+len(info.extra);h=hashlib.sha256();n=0
  with z.open(info,'w') as dest:
   for b in model_parts(man):dest.write(b);h.update(b);n+=len(b)
  assert n==man['pack']['bytes'] and h.hexdigest()==PACK_SHA
 loc={'path':str(unsigned),'offset':offset,'length':n,'sha256':PACK_SHA,'source':'preserved general best, all546text tensors'};(HERE/'reports/model_locator.json').write_text(json.dumps(loc,indent=2)+'\n');print('PARENT_PACK_PREPARED',n,flush=True)
def seal(existing_config=False):
 unsigned=OUT/'unsigned.apk';assert unsigned.exists();final=OUT/'LiquidSense-0.4.0-thinking-preview.apk';assert not final.exists();use=False;config={'use_validated_dense':use,'model_parent':'general_best','neural_loop_visits':56,'physical_layers':32,'tools_variant':'native_supervised023' if use else 'preserved_general_tools_runtime','experimental':True,'general_quality_promotion':False,'context_tokens':16384,'generation_presets':{'normal':{'thinking':False,'reasoning_tokens':0,'response_tokens':2048},'profundo':{'thinking':True,'reasoning_tokens':1024,'response_tokens':2048},'extenso':{'thinking':True,'reasoning_tokens':2048,'response_tokens':4096}},'default_general_profile':'normal','agent_max_rounds':6,'agent_max_actual_tools':4,'task_output_limit':16384}
 with zipfile.ZipFile(unsigned,'a',allowZip64=False) as z:
  # Staging may precede the final native rebuild; replace only unsigned library.
  native=Path('/dev/shm/liquid-android/prebuilt/thinking024/libliquid_sense.so').read_bytes();entry='lib/arm64-v8a/libliquid_sense.so';old=z.getinfo(entry)
  if z.read(old)!=native:
   z.filelist.remove(old);del z.NameToInfo[entry];z.writestr(aligned_info(z,entry,len(native),zipfile.ZIP_DEFLATED),native)
  assert hashlib.sha256(z.read(entry)).hexdigest()==hashlib.sha256(native).hexdigest()
  for dex in Path('/dev/shm/liquid-android/thinking024/ui/dex').glob('*.dex'):
   old=z.getinfo(dex.name);payload=dex.read_bytes()
   if z.read(old)!=payload:
    z.filelist.remove(old);del z.NameToInfo[dex.name];z.writestr(aligned_info(z,dex.name,len(payload),zipfile.ZIP_DEFLATED),payload)
   assert z.read(dex.name)==payload
  assert len(z.namelist())==len(set(z.namelist())), 'Never ship duplicate ZIP entry names'
  present='assets/build_config.json' in z.namelist();assert not present or existing_config,'Inspect partial sealing state'
  if use:
   chosen=json.loads((HERE/'candidate_artifact.json').read_text());m=json.loads((HERE/chosen['metadata']).read_text());p=HERE/chosen['weights'];assert sha(p)==m['sha256'];config['dense_sha256']=m['sha256'];z.writestr(aligned_info(z,'assets/down_proj.bf16.bin',p.stat().st_size,zipfile.ZIP_STORED),p.read_bytes())
  if present:assert json.loads(z.read('assets/build_config.json'))==config
  else:
   payload=json.dumps(config,separators=(',',':')).encode();z.writestr(aligned_info(z,'assets/build_config.json',len(payload),zipfile.ZIP_STORED),payload)
 run(BT/'zipalign','-c','-P','16','4',unsigned)
 with unsigned.open('rb') as f:f.seek(-min(65557,unsigned.stat().st_size),2);tail=f.read();end=tail.rfind(b'PK\x05\x06');assert end>=0;boundary=struct.unpack_from('<I',tail,end+16)[0]
 classes=OUT/'signclasses';classes.mkdir(exist_ok=True);jar=BT/'lib/apksigner.jar';run('java','com.sun.tools.javac.Main','-classpath',jar,'-d',classes,ROOT/'android_models021/tools/TailSigner.java');run('java','-cp',str(classes)+':'+str(jar),'TailSigner',unsigned,str(boundary),'/tmp/liquid-fast020-signing/preview.p12','/tmp/liquid-fast020-signing/password');unsigned.rename(final)
 for name,args in [('signature.txt',['java','-jar',jar,'verify','--verbose','--print-certs',final]),('badging.txt',[BT/'aapt2','dump','badging',final]),('permissions.txt',[BT/'aapt2','dump','permissions',final])]:
  r=subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True,env=ENV);(HERE/'reports'/name).write_text(r.stdout)
 run(BT/'zipalign','-c','-P','16','4',final);assert 'android.permission.INTERNET' in (HERE/'reports/permissions.txt').read_text();assert 'fcb504e5004b8e0be879b952d597248da3a731c481c1f24cd1ac01502df5ac5b' in (HERE/'reports/signature.txt').read_text()
 with zipfile.ZipFile(final) as z:
  assert z.testzip() is None,'APK entry CRC failure'
  assert z.getinfo('assets/model.lsp').compress_type==zipfile.ZIP_STORED
  with z.open('assets/model.lsp') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==PACK_SHA
  assert json.loads(z.read('assets/build_config.json'))==config
 loc=json.loads((HERE/'reports/model_locator.json').read_text());loc['path']=str(final);(HERE/'reports/model_locator.json').write_text(json.dumps(loc,indent=2)+'\n')
 report={'status':'signed_tools_APK_built','path':str(final),'bytes':final.stat().st_size,'sha256':sha(final),'package':'dev.liquidsense.chat.tools','separate_app_preserves_specialist_and_original':True,'versionCode':2,'parent_pack_sha256':PACK_SHA,'config':config,'phone_execution_verified':False,'specialist_option':'uses optional installed dev.liquidsense.chat.fast public assets','base_general_fully_bundled':True};(HERE/'reports/apk_manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('TOOLS_APK_SIGNED',json.dumps(report),flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['prepare','seal']);ap.add_argument('--existing-config',action='store_true');a=ap.parse_args();prepare() if a.phase=='prepare' else seal(a.existing_config)
