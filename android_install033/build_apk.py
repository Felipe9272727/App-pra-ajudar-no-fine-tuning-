"""Fresh canonical APK, never append/replace ZIP entries of a signed release."""
import hashlib,json,os,struct,subprocess,sys,zipfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
H=ROOT/'android_install033';OUT=Path('/dev/shm/liquid-android/install033-apk');UI=Path('/dev/shm/liquid-android/install033/ui');CACHE=OUT/'shared'
from android_epochs030.build_apk import sha,BT
from android_models021.tools.build_apk import aligned_info
from android_ui032.archive_apk import blocks
from tooluse022.archive_apks import model_parts
ENV={**os.environ,'LD_LIBRARY_PATH':str(BT/'lib64'),'JAVA_TOOL_OPTIONS':'-Xmx768m'}
def run(*args):subprocess.run([str(a) for a in args],check=True,env=ENV)
def save(name,data):(H/'reports'/name).write_text(json.dumps(data,indent=2)+'\n')
def main():
    OUT.mkdir(exist_ok=True);CACHE.mkdir(exist_ok=True);unsigned=OUT/'unsigned.apk';final=OUT/'LiquidSense-0.6.3-install-preview.apk';assert not unsigned.exists() and not final.exists(),'Inspect interrupted build'
    prior=json.loads((ROOT/'android_ui032/reports/apk_manifest.json').read_text());old=Path(prior['path']);assert sha(old)==prior['sha256']
    arc=json.loads((ROOT/'android_ui032/apk_archive/manifest.json').read_text());check=hashlib.sha256()
    for s in arc['segments']:
        for b in blocks(s):check.update(b)
    assert check.hexdigest()==prior['sha256'];small=[]
    with zipfile.ZipFile(old) as z:
        for i in z.infolist():
            if not i.filename.startswith(('assets/','lib/')) or i.filename in ['assets/model.lsp','assets/epoch02.lspatch'] or i.filename.startswith('assets/chat/'):continue
            target=CACHE/i.filename;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(i));small.append(i.filename)
    patch=Path('/dev/shm/liquid-android/epochs030/epoch02.lspatch');assert sha(patch)==prior['experimental_patch_sha256']
    config=json.loads((CACHE/'assets/build_config.json').read_text());config.update(ui_version='0.6.3',canonical_fresh_ZIP=True,signing_schemes=['v1','v2','v3']);(CACHE/'assets/build_config.json').write_text(json.dumps(config,separators=(',',':')))
    save('previous_APK_preservation.json',{'old_SHA256':prior['sha256'],'immutable_archive_commit':'64e8e4d11a166b508235e8dd22f7bd632a345c30','archive':'android_ui032/apk_archive/manifest.json','full_reconstruction_verified':True,'logical_shared_payloads_extracted':small,'retired_only_redundant_RAM_build_cache':str(old),'no_checkpoints_removed':True})
    old.unlink() # Exact old signed bytes remain in verified immutable archive + public download.
    pack=json.loads((ROOT/'tooluse022/apk_archive/manifest.json').read_text())
    with zipfile.ZipFile(unsigned,'w',allowZip64=False) as z:
        def put(name,data,kind=zipfile.ZIP_DEFLATED):z.writestr(aligned_info(z,name,len(data),kind),data)
        with zipfile.ZipFile(UI/'resources.apk') as res:
            infos=sorted(res.infolist(),key=lambda i:(i.filename!='AndroidManifest.xml',i.filename))
            for i in infos:put(i.filename,res.read(i),zipfile.ZIP_STORED if i.filename=='resources.arsc' else i.compress_type)
        for dex in (UI/'dex').glob('*.dex'):put(dex.name,dex.read_bytes())
        for name in sorted(small):
            raw=(CACHE/name).read_bytes();put(name,raw,zipfile.ZIP_STORED if name=='assets/tokenizer.json' else zipfile.ZIP_DEFLATED)
        for p in sorted((H/'android/assets').rglob('*')):
            if p.is_file():put('assets/'+p.relative_to(H/'android/assets').as_posix(),p.read_bytes())
        for name,size,expected,source in [('assets/model.lsp',pack['pack']['bytes'],prior['parent_pack_sha256'],model_parts(pack)),('assets/epoch02.lspatch',patch.stat().st_size,prior['experimental_patch_sha256'],iter_file(patch))]:
            h=hashlib.sha256();count=0
            with z.open(aligned_info(z,name,size,zipfile.ZIP_STORED),'w') as dst:
                for b in source:dst.write(b);h.update(b);count+=len(b)
            assert count==size and h.hexdigest()==expected
        assert len(z.namelist())==len(set(z.namelist()))
    run(BT/'zipalign','-c','-P','16','4',unsigned)
    with zipfile.ZipFile(unsigned) as z:boundary=z.start_dir
    classes=OUT/'signclasses';classes.mkdir(exist_ok=True);jar=BT/'lib/apksigner.jar'
    run('java','com.sun.tools.javac.Main','-classpath',jar,'-d',classes,H/'CleanSigner.java');run('java','-cp',str(classes)+':'+str(jar),'CleanSigner',unsigned,str(boundary),'/tmp/liquid-fast020-signing/preview.p12','/tmp/liquid-fast020-signing/password');unsigned.rename(final)
    verify()
def verify():
    final=OUT/'LiquidSense-0.6.3-install-preview.apk';jar=BT/'lib/apksigner.jar';prior=json.loads((ROOT/'android_ui032/reports/apk_manifest.json').read_text())
    for name,args in [('signature.txt',['java','-jar',jar,'verify','--verbose','--print-certs',final]),('badging.txt',[BT/'aapt2','dump','badging',final]),('permissions.txt',[BT/'aapt2','dump','permissions',final])]:
        r=subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True,env=ENV);(H/'reports'/name).write_text(r.stdout)
    sig=(H/'reports/signature.txt').read_text()
    for name,low,high,expected in [('v1',21,23,'v1 scheme (JAR signing)'),('v2',24,27,'v2 scheme (APK Signature Scheme v2)'),('v3',28,35,'v3 scheme (APK Signature Scheme v3)')]:
        r=subprocess.run(['java','-jar',str(jar),'verify','--verbose','--min-sdk-version',str(low),'--max-sdk-version',str(high),str(final)],check=True,capture_output=True,text=True,env=ENV);(H/'reports'/('signature_'+name+'.txt')).write_text(r.stdout);assert 'Verified using '+expected+': true' in r.stdout
    assert 'fcb504e5004b8e0be879b952d597248da3a731c481c1f24cd1ac01502df5ac5b' in sig
    run(BT/'zipalign','-c','-P','16','4',final)
    with zipfile.ZipFile(final) as z:
        assert z.testzip() is None
        for name,expected in [('assets/model.lsp',prior['parent_pack_sha256']),('assets/epoch02.lspatch',prior['experimental_patch_sha256'])]:
            with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
        native={}
        for name,expected in prior['native_libraries_unchanged'].items():native[name]=hashlib.sha256(z.read(name)).hexdigest();assert native[name]==expected
    report={'status':'fresh_canonical_signed_APK_built','path':str(final),'bytes':final.stat().st_size,'sha256':sha(final),'package':prior['package'],'versionCode':7,'versionName':'0.6.3-install-preview','parent_pack_sha256':prior['parent_pack_sha256'],'experimental_patch_sha256':prior['experimental_patch_sha256'],'native_libraries_unchanged':native,'signing_schemes':['v1','v2','v3'],'same_previous_certificate':True,'previous_APK_sha256':prior['sha256'],'no_inherited_ZIP_records_or_signing_blocks':True,'phone_execution_verified':False,'emulator_installation':'pending'};save('apk_manifest.json',report);print(json.dumps(report),flush=True)
def iter_file(p):
    with p.open('rb') as f:
        while b:=f.read(4*1024*1024):yield b
if __name__=='__main__':verify() if '--verify-existing' in sys.argv else main()
