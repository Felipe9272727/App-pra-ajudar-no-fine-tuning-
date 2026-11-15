"""Repackage the verified030 build cache in place; old signed bytes stay archived."""
import hashlib,json,struct,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));H=ROOT/'android_ui031';OUT=Path('/dev/shm/liquid-android/ui031-061-apk');UI=Path('/dev/shm/liquid-android/ui031/ui')
from android_epochs030.build_apk import sha,run,BT,ENV
from android_models021.tools.build_apk import aligned_info
def save(name,data):(H/'reports'/name).write_text(json.dumps(data,indent=2)+'\n')
def main():
    OUT.mkdir(exist_ok=True);unsigned=OUT/'unsigned.apk';final=OUT/'LiquidSense-0.6.1-ui-preview.apk'
    assert not unsigned.exists() and not final.exists(),'Inspect interrupted packaging before continuing'
    prior=json.loads((ROOT/'android_epochs030/reports/apk_manifest.json').read_text());old=Path(prior['path']);assert sha(old)==prior['sha256']
    subprocess.run([sys.executable,'android_epochs030/verify_archive.py'],cwd=ROOT,check=True)
    save('previous_APK_preservation.json',{'old_APK_sha256':prior['sha256'],'exact_archive':'android_epochs030/apk_archive/manifest.json','verified_remote_commit':'3a73e4795bdbdcd9a14479336416aa04d75d6fd5','full_reconstruction_stream_verified':True,'retiring_only_redundant_RAM_build_copy':str(old),'checkpoint_and_archives_deleted':False})
    before={}
    with zipfile.ZipFile(old) as z:
        for name in ['lib/arm64-v8a/libliquid_sense.so','lib/arm64-v8a/libliquid_python.so']:
            before[name]=hashlib.sha256(z.read(name)).hexdigest()
        config=json.loads(z.read('assets/build_config.json'));config.update(ui_version='0.6.1',local_webview=True,UI_only_release=True)
    old.rename(unsigned) # Zero-copy cache reuse, with old signed APK fully recoverable.
    with zipfile.ZipFile(unsigned,'a',allowZip64=False) as z:
        def put(name,data,kind=zipfile.ZIP_DEFLATED):
            if name in z.NameToInfo:
                old=z.getinfo(name)
                if z.read(old)==data:return
                z.filelist.remove(old);del z.NameToInfo[name]
            z.fp.seek(z.start_dir)
            z.writestr(aligned_info(z,name,len(data),kind),data)
        with zipfile.ZipFile(UI/'resources.apk') as res:
            for info in res.infolist():put(info.filename,res.read(info),info.compress_type)
        for dex in (UI/'dex').glob('*.dex'):put(dex.name,dex.read_bytes())
        for p in sorted((H/'android/assets').rglob('*')):
            if p.is_file():put('assets/'+p.relative_to(H/'android/assets').as_posix(),p.read_bytes())
        put('assets/build_config.json',json.dumps(config,separators=(',',':')).encode(),zipfile.ZIP_STORED)
        assert len(z.namelist())==len(set(z.namelist()))
    seal(prior,before,config)
def seal(prior,before,config):
    unsigned=OUT/'unsigned.apk';final=OUT/'LiquidSense-0.6.1-ui-preview.apk'
    run(BT/'zipalign','-c','-P','16','4',unsigned)
    with unsigned.open('rb') as f:f.seek(-min(65557,unsigned.stat().st_size),2);tail=f.read();end=tail.rfind(b'PK\x05\x06');boundary=struct.unpack_from('<I',tail,end+16)[0]
    classes=OUT/'signclasses';classes.mkdir(exist_ok=True);jar=BT/'lib/apksigner.jar'
    run('java','com.sun.tools.javac.Main','-classpath',jar,'-d',classes,ROOT/'android_models021/tools/TailSigner.java');run('java','-cp',str(classes)+':'+str(jar),'TailSigner',unsigned,str(boundary),'/tmp/liquid-fast020-signing/preview.p12','/tmp/liquid-fast020-signing/password');unsigned.rename(final)
    for name,args in [('signature.txt',['java','-jar',jar,'verify','--verbose','--print-certs',final]),('badging.txt',[BT/'aapt2','dump','badging',final]),('permissions.txt',[BT/'aapt2','dump','permissions',final])]:
        r=subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True,env=ENV);(H/'reports'/name).write_text(r.stdout)
    assert 'fcb504e5004b8e0be879b952d597248da3a731c481c1f24cd1ac01502df5ac5b' in (H/'reports/signature.txt').read_text()
    assert "versionCode='5'" in (H/'reports/badging.txt').read_text();run(BT/'zipalign','-c','-P','16','4',final)
    with zipfile.ZipFile(final) as z:
        assert z.testzip() is None
        for name,expected in before.items():assert hashlib.sha256(z.read(name)).hexdigest()==expected
        for name,expected in [('assets/model.lsp',prior['parent_pack_sha256']),('assets/epoch02.lspatch',prior['experimental_patch_sha256'])]:
            assert z.getinfo(name).compress_type==zipfile.ZIP_STORED
            with z.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
        for p in (H/'android/assets').rglob('*'):
            if p.is_file():assert z.read('assets/'+p.relative_to(H/'android/assets').as_posix())==p.read_bytes()
    report={'status':'signed_UI031_APK_verified','path':str(final),'bytes':final.stat().st_size,'sha256':sha(final),'package':'dev.liquidsense.chat.tools','versionCode':5,'versionName':'0.6.1-ui-preview','previous_APK_sha256':prior['sha256'],'native_libraries_unchanged':before,'parent_pack_sha256':prior['parent_pack_sha256'],'experimental_patch_sha256':prior['experimental_patch_sha256'],'new_training_updates':0,'same_previous_certificate':True,'phone_execution_verified':False,'UI_compiled':True,'all_ZIP_CRC_verified':True,'config':config};report['weight_runtime_reference_APK_sha256']=prior['sha256'];report['previous_APK_sha256']=json.loads((H/'releases/0.6.0/apk_manifest.json').read_text())['sha256'] if config.get('ui_version')=='0.6.1' else prior['sha256'];save('apk_manifest.json',report);print(json.dumps(report),flush=True)
def resume():
    unsigned=OUT/'unsigned.apk';assert unsigned.exists() and not (OUT/'LiquidSense-0.6.1-ui-preview.apk').exists()
    prior=json.loads((ROOT/'android_epochs030/reports/apk_manifest.json').read_text());saved=json.loads((H/'reports/previous_APK_preservation.json').read_text());assert saved['old_APK_sha256']==prior['sha256']
    expected={'lib/arm64-v8a/libliquid_sense.so':sha(Path('/dev/shm/liquid-android/prebuilt/epochs030/libliquid_sense.so')),'lib/arm64-v8a/libliquid_python.so':json.loads((ROOT/'tooluse023/artifacts/python_arm.json').read_text())['raw_sha256']}
    repaired=[]
    with zipfile.ZipFile(unsigned,'a',allowZip64=False) as z:
        config=json.loads(z.read('assets/build_config.json'));assert config['ui_version']=='0.6.1'
        for name,value in expected.items():assert hashlib.sha256(z.read(name)).hexdigest()==value
        for info in list(z.infolist()):
            if info.compress_type!=zipfile.ZIP_STORED:continue
            with unsigned.open('rb') as f:f.seek(info.header_offset+26);nl,el=struct.unpack('<HH',f.read(4))
            if (info.header_offset+30+nl+el)%4:
                assert info.file_size<1024*1024,'Never move/rewrite large model assets during alignment recovery'
                raw=z.read(info);z.filelist.remove(info);del z.NameToInfo[info.filename];z.fp.seek(z.start_dir);z.writestr(aligned_info(z,info.filename,len(raw),info.compress_type),raw);repaired.append(info.filename)
    save('alignment_recovery.json',{'cause':'append-mode reader moved file pointer before calculating resource padding','repaired_small_entries':repaired,'large_model_assets_unchanged':True,'no_training_or_inference_restarted':True})
    seal(prior,expected,config)
def refresh_ui():
    OUT.mkdir(exist_ok=True);m=json.loads((H/'releases/0.6.0/apk_manifest.json').read_text());old=Path(m['path']);assert sha(old)==m['sha256']
    # The delivered0.6.0 remains exactly recoverable from the verified immutable archive.
    from archive_apk import blocks
    preserved=json.loads((H/'apk_archive/manifest.json').read_text());digest=hashlib.sha256()
    for segment in preserved['segments']:
        for block in blocks(segment):digest.update(block)
    assert digest.hexdigest()==m['sha256'];save('commands_previous_APK_preservation.json',{'old_SHA256':m['sha256'],'archive':'android_ui031/apk_archive/manifest.json','immutable_commit':'883281cca5377a7e0e90fe818e410cba2de327a6','full_reconstruction_verified':True,'only_redundant_build_cache_reused':True})
    unsigned=OUT/'unsigned.apk';assert not unsigned.exists();old.rename(unsigned)
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
        config=json.loads(z.read('assets/build_config.json'));config.update(ui_version='0.6.1',local_slash_commands=True);put('assets/build_config.json',json.dumps(config,separators=(',',':')).encode(),zipfile.ZIP_STORED)
    prior=json.loads((ROOT/'android_epochs030/reports/apk_manifest.json').read_text())
    seal(prior,m['native_libraries_unchanged'],config)
if __name__=='__main__':
    if '--refresh-ui' in sys.argv:refresh_ui()
    elif '--resume' in sys.argv:resume()
    else:main()
