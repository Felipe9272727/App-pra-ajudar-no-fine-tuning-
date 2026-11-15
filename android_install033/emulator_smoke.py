"""Actual adb PackageManager install/update/launch evidence on an owned CI emulator."""
import json,os,subprocess,time,sys
from pathlib import Path
from portable_restore import restore
H=Path(__file__).resolve().parent;OUT=Path(os.environ['RUNNER_TEMP'])/'install033-evidence';OUT.mkdir(exist_ok=True);TEMP=Path(os.environ['RUNNER_TEMP']);PKG='dev.liquidsense.chat.tools'
def adb(*args,timeout=180):return subprocess.run(['adb',*args],capture_output=True,text=True,timeout=timeout)
def save(name,text):(OUT/name).write_text(text)
def install(manifest,name):
    path=TEMP/name;restore(manifest,path);r=adb('install','--no-incremental','-r',str(path));save(name+'.install.txt',r.stdout+r.stderr);ok=r.returncode==0 and 'Success'in r.stdout;path.unlink();return ok,r.stdout+r.stderr
def main():
    props=adb('shell','getprop');save('properties.txt',props.stdout)
    old_ok,old_log=install('android_ui032/apk_archive/manifest.json','old062.apk')
    baseline=old_ok
    if not baseline:baseline,_=install('android_ui031/apk_archive/manifest.json','baseline060.apk')
    # Owned Google-APIs emulator is userdebug; test private-data preservation, no user data involved.
    rooted=False
    if baseline:
        root=adb('root');adb('wait-for-device');save('adb-root.txt',root.stdout+root.stderr)
        marker=adb('shell','sh','-c',f"'mkdir -p /data/user/0/{PKG}/files; echo install033-preserve > /data/user/0/{PKG}/files/install033-marker'")
        uid=adb('shell','stat','-c','%u',f'/data/user/0/{PKG}').stdout.strip()
        if marker.returncode==0 and uid.isdigit():
            adb('shell','chown','-R',uid+':'+uid,f'/data/user/0/{PKG}/files');adb('shell','restorecon','-R',f'/data/user/0/{PKG}/files')
        rooted=marker.returncode==0;save('marker-create.txt',marker.stdout+marker.stderr)
    new_ok,new_log=install('android_install033/apk_archive/manifest.json','new063.apk')
    result={'old062_installed':old_ok,'old062_installer_output':old_log,'baseline_available':baseline,'new063_installed':new_ok,'new063_installer_output':new_log,'scope':'actual Android emulator PackageManager; not physical Xiaomi','source_manifest':'android_install033/apk_archive/manifest.json'}
    if new_ok and rooted:
        marker=adb('shell','cat',f'/data/user/0/{PKG}/files/install033-marker');result['private_data_preserved_on_update']=marker.stdout.strip()=='install033-preserve';save('update-marker.txt',marker.stdout+marker.stderr)
    if new_ok:
        r=adb('shell','am','start','-W','-n',PKG+'/dev.liquidsense.chat.MainActivity',timeout=90);save('launch.txt',r.stdout+r.stderr)
        result['activity_start_command_success']=r.returncode==0 and 'Error:'not in r.stdout+r.stderr
        time.sleep(20);pid=adb('shell','pidof',PKG);result['app_process_alive_after20s']=bool(pid.stdout.strip());save('pid.txt',pid.stdout+pid.stderr)
        adb('shell','uiautomator','dump','/sdcard/ui033.xml',timeout=45);adb('pull','/sdcard/ui033.xml',str(OUT/'ui.xml'))
        adb('shell','screencap','-p','/sdcard/screen033.png');adb('pull','/sdcard/screen033.png',str(OUT/'screen.png'))
        adb('shell','dumpsys','package',PKG);save('package.txt',adb('shell','dumpsys','package',PKG).stdout)
    save('logcat.txt',adb('logcat','-d','-t','2500').stdout)
    save('result.json',json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    assert new_ok,'New full APK rejected by actual Android PackageManager'
    if rooted:assert result['private_data_preserved_on_update'],'Private data not preserved'
if __name__=='__main__':main()
