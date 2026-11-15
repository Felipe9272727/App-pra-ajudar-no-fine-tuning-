"""UI032update: preserve exact031archive, reuse only verified redundant build cache."""
import hashlib,json,struct,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));H=ROOT/'android_ui032';OUT=Path('/dev/shm/liquid-android/ui032-apk');UI=Path('/dev/shm/liquid-android/ui032/ui')
from android_epochs030.build_apk import sha,run,BT,ENV
from android_models021.tools.build_apk import aligned_info
from android_ui031.archive_apk import blocks
def save(name,data):(H/'reports'/name).write_text(json.dumps(data,indent=2)+'\n')
def main():
    OUT.mkdir(exist_ok=True);unsigned=OUT/'unsigned.apk';assert not unsigned.exists() and not (OUT/'LiquidSense-0.6.2-ui-preview.apk').exists(),'Inspect interrupted packaging'
    prior=json.loads((ROOT/'android_ui031/reports/apk_manifest.json').read_text());old=Path(prior['path']);assert sha(old)==prior['sha256']
    arc=json.loads((ROOT/'android_ui031/apk_archive_061/manifest.json').read_text());check=hashlib.sha256()
    for segment in arc['segments']:
        for raw in blocks(segment):check.update(raw)
    assert check.hexdigest()==prior['sha256'];save('previous_APK_preservation.json',{'old_SHA256':prior['sha256'],'archive':'android_ui031/apk_archive_061/manifest.json','immutable_commit':'c37e62b9a3f8d40bdffad33a2e5bd0edd7052878','full_reconstruction_verified':True,'only_redundant_RAM_build_cache_reused':True})
    with zipfile.ZipFile(old) as z:config=json.loads(z.read('assets/build_config.json'))
    config.update(ui_version='0.6.2',IME_native_insets=True,pending_navigation=True,UI_motion=True)
    old.rename(unsigned)
    with zipfile.ZipFile(unsigned,'a',allowZip64=False) as z:
        def put(name,data,kind=zipfile.ZIP_DEFLATED):
            if name in z.NameToInfo:
                previous=z.getinfo(name)
                if z.read(previous)==data:return
                z.filelist.remove(previous);del z.NameToInfo[name]
            z.fp.seek(z.start_dir);z.writestr(aligned_info(z,name,len(data),kind),data)
        with zipfile.ZipFile(UI/'resources.apk') as res:
            for i in res.infolist():put(i.filename,res.read(i),i.compress_type)
        for dex in (UI/'dex').glob('*.dex'):put(dex.name,dex.read_bytes())
        for p in (H/'android/assets').rglob('*'):
            if p.is_file():put('assets/'+p.relative_to(H/'android/assets').as_posix(),p.read_bytes())
        put('assets/build_config.json',json.dumps(config,separators=(',',':')).encode(),zipfile.ZIP_STORED)
        assert len(z.namelist())==len(set(z.namelist()))
    seal(prior,prior['native_libraries_unchanged'],config)
def seal(prior,before,config):
    unsigned=OUT/'unsigned.apk';final=OUT/'LiquidSense-0.6.2-ui-preview.apk'
    run(BT/'zipalign','-c','-P','16','4',unsigned)
    with unsigned.open('rb') as f:f.seek(-min(65557,unsigned.stat().st_size),2);tail=f.read();end=tail.rfind(b'PK\x05\x06');boundary=struct.unpack_from('<I',tail,end+16)[0]
    classes=OUT/'signclasses';classes.mkdir(exist_ok=True);jar=BT/'lib/apksigner.jar'
    run('java','com.sun.tools.javac.Main','-classpath',jar,'-d',classes,ROOT/'android_models021/tools/TailSigner.java');run('java','-cp',str(classes)+':'+str(jar),'TailSigner',unsigned,str(boundary),'/tmp/liquid-fast020-signing/preview.p12','/tmp/liquid-fast020-signing/password');unsigned.rename(final)
    for name,args in [('signature.txt',['java','-jar',jar,'verify','--verbose','--print-certs',final]),('badging.txt',[BT/'aapt2','dump','badging',final]),('permissions.txt',[BT/'aapt2','dump','permissions',final])]:
        r=subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True,env=ENV);(H/'reports'/name).write_text(r.stdout)
    assert 'fcb504e5004b8e0be879b952d597248da3a731c481c1f24cd1ac01502df5ac5b' in (H/'reports/signature.txt').read_text()
    assert "versionCode='6'" in (H/'reports/badging.txt').read_text();run(BT/'zipalign','-c','-P','16','4',final)
    with zipfile.ZipFile(final) as z:
        assert z.testzip() is None
        for name,expected in before.items():assert hashlib.sha256(z.read(name)).hexdigest()==expected
        for name,expected in [('assets/model.lsp',prior['parent_pack_sha256']),('assets/epoch02.lspatch',prior['experimental_patch_sha256'])]:
            assert z.getinfo(name).compress_type==zipfile.ZIP_STORED
            with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
        for p in (H/'android/assets').rglob('*'):
            if p.is_file():assert z.read('assets/'+p.relative_to(H/'android/assets').as_posix())==p.read_bytes()
    report={'status':'signed_UI032_APK_verified','path':str(final),'bytes':final.stat().st_size,'sha256':sha(final),'package':'dev.liquidsense.chat.tools','versionCode':6,'versionName':'0.6.2-ui-preview','previous_APK_sha256':prior['sha256'],'native_libraries_unchanged':before,'parent_pack_sha256':prior['parent_pack_sha256'],'experimental_patch_sha256':prior['experimental_patch_sha256'],'new_training_updates':0,'same_previous_certificate':True,'phone_execution_verified':False,'UI_compiled':True,'all_ZIP_CRC_verified':True,'config':config};report['weight_runtime_reference_APK_sha256']=prior['weight_runtime_reference_APK_sha256'];save('apk_manifest.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':main()
