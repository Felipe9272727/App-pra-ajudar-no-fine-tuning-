"""Build the update helper and optional same-signed installation test APKs."""
import json
import shutil
import zipfile
from build_apk import HERE, OUT, SDK, BT, SECRET, SIGNER_SHA, run, sha, put


def build(source, name, assets=None):
    out = OUT / source.name
    classes, dex = out / 'classes', out / 'dex'
    classes.mkdir(parents=True,exist_ok=True); dex.mkdir(exist_ok=True)
    intermediates = out / 'resources.apk'
    jar = SDK / 'platform/android.jar'
    link = [BT / 'aapt2', 'link', '-o', intermediates, '--manifest', source / 'AndroidManifest.xml', '-I', jar]
    if (source / 'res').exists():
        compiled = out / 'resources.zip'
        run(BT / 'aapt2', 'compile', '--dir', source / 'res', '-o', compiled)
        link.extend(['-R', compiled, '--auto-add-overlay'])
    run(*link)
    run('java','com.sun.tools.javac.Main','-source','8','-target','8','-classpath',jar,'-d',classes,*source.rglob('*.java'))
    run('java','-cp',BT/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',jar,'--output',dex,*classes.rglob('*.class'))
    unsigned = out / 'unsigned.apk'
    final = OUT / name
    with zipfile.ZipFile(unsigned,'w') as target, zipfile.ZipFile(intermediates) as resources:
        for entry in sorted(resources.infolist(),key=lambda item:(item.filename!='AndroidManifest.xml',item.filename)):
            kind = zipfile.ZIP_STORED if entry.filename == 'resources.arsc' else zipfile.ZIP_DEFLATED
            put(target, entry.filename, resources.read(entry), kind)
        for entry in dex.glob('*.dex'):
            put(target, entry.name, entry.read_bytes(), zipfile.ZIP_DEFLATED)
        for path, content in (assets or {}).items():
            put(target, path, content, zipfile.ZIP_STORED)
    run(BT/'zipalign','-c','4',unsigned)
    jar = BT / 'lib/apksigner.jar'
    run('java','-jar',jar,'sign','--ks',SECRET/'preview.p12','--ks-key-alias','liquid-sense-fast',
        '--ks-pass',f'file:{SECRET / "password"}','--min-sdk-version','28','--v1-signing-enabled','true',
        '--v2-signing-enabled','true','--v3-signing-enabled','true','--out',final,unsigned)
    result = run('java','-jar',jar,'verify','--verbose','--print-certs',final)
    assert SIGNER_SHA in result
    run(BT/'zipalign','-c','4',final)
    with zipfile.ZipFile(final) as z:assert z.testzip() is None
    return {'name': name, 'bytes': final.stat().st_size, 'sha256': sha(final)}


def main():
    with zipfile.ZipFile(OUT / 'delta.zip') as delta:
        manifest = delta.read('manifest.json')
    output = {'updater': build(HERE / 'updater', 'LiquidSense-Atualizador-0.5.apk', {
        'assets/delta.zip': (OUT / 'delta.zip').read_bytes(), 'assets/delta-manifest.json': manifest,
    })}
    for source in ('smoke_updater', 'smoke_chat'):
        if (HERE/source).exists():
            name = source + '.apk'
            output[source] = build(HERE / source, name)
            destination = HERE / 'tests'
            destination.mkdir(exist_ok=True)
            shutil.copyfile(OUT / name, destination / (name + '.bin'))
    (HERE/'reports/updater_manifest.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output),flush=True)

if __name__=='__main__':main()
