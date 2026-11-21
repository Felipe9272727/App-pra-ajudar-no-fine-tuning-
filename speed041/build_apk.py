"""Rebuild the Android app and produce a compact patch for the installed copy."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent

OUT = Path('/dev/shm/speed041')
SDK = Path('/dev/shm/liquid-android/tooling/android')
BT = SDK / 'build-tools'
UI = Path('/dev/shm/liquid-android/speed041/ui')
OLD = Path('/dev/shm/online040/LiquidSense-0.6.4-gpu-preview.apk')
NATIVE = OUT / 'libliquid_sense.so'
NATIVE_ENTRY = 'lib/arm64-v8a/libliquid_sense.so'
FINAL = OUT / 'LiquidSense-0.6.5-speed-preview.apk'
OLD_SHA = 'd005159c879f86d1fcf007f9660ce6a56d008be57eafbda0946c03e0272ee746'
SIGNER_SHA = 'fcb504e5004b8e0be879b952d597248da3a731c481c1f24cd1ac01502df5ac5b'
SECRET = Path('/tmp/liquid-fast020-signing')
ENV = {**os.environ, 'LD_LIBRARY_PATH': str(BT / 'lib64'), 'JAVA_TOOL_OPTIONS': '-Xmx512m'}
LARGE = ('assets/model.lsp', 'assets/epoch02.lspatch')


def run(*command):
    return subprocess.check_output([str(v) for v in command], text=True, env=ENV)


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def aligned_info(z,name,size,kind):
 x=zipfile.ZipInfo(name,date_time=(2026,11,12,0,0,0));x.compress_type=kind;x.file_size=size;offset=z.fp.tell()+30+len(name.encode())
 if kind==zipfile.ZIP_STORED and offset%4:
  pad=(-(offset+4))%4;x.extra=struct.pack('<HH',0xFFFF,pad)+bytes(pad)
 return x


def put(z, name, data, kind):
    z.writestr(aligned_info(z, name, len(data), kind), data)


def verify(apk):
    run(BT / 'zipalign', '-c', '-P', '16', '4', apk)
    for name, low, high in [('v1', 21, 23), ('v2', 24, 27), ('v3', 28, 35)]:
        sig = run('java', '-jar', BT / 'lib/apksigner.jar', 'verify', '--verbose', '--print-certs',
                  '--min-sdk-version', low, '--max-sdk-version', high, apk)
        assert f'Verified using {name} scheme ' in sig and any(
            line.startswith(f'Verified using {name} scheme ') and line.endswith(': true') for line in sig.splitlines())
        assert SIGNER_SHA in sig
        (HERE / f'reports/apk_{name}.txt').write_text(sig)
    badging = run(BT / 'aapt2', 'dump', 'badging', apk)
    assert "versionCode='9'" in badging and "name='dev.liquidsense.chat.tools'" in badging
    (HERE / 'reports/badging.txt').write_text(badging)
    retained = {}
    with zipfile.ZipFile(apk) as new, zipfile.ZipFile(OLD) as old:
        assert new.testzip() is None
        for name in new.namelist():
            if name == NATIVE_ENTRY:
                with new.open(name) as native:
                    assert hashlib.file_digest(native, 'sha256').hexdigest() == sha(NATIVE)
                continue
            if name.startswith('lib/') or (name.startswith('assets/') and name != 'assets/build_config.json'
                                           and not name.startswith('assets/chat/')):
                with new.open(name) as one, old.open(name) as two:
                    first = hashlib.file_digest(one, 'sha256').hexdigest()
                    assert first == hashlib.file_digest(two, 'sha256').hexdigest(), name
                    retained[name] = first
    return {'bytes': apk.stat().st_size,'sha256': sha(apk),'version_code': 9, 'unchanged_assets': retained,
            'installed_base_sha256': OLD_SHA, 'signer_sha256': SIGNER_SHA, 'native_sha256': sha(NATIVE)}


def make_apk():
    assert sha(OLD) == OLD_SHA
    if FINAL.exists():
        return verify(FINAL)
    unsigned = OUT / 'unsigned-online.apk'
    if unsigned.exists():
        raise FileExistsError('Inspect the previous unsigned build before restarting')
    with zipfile.ZipFile(unsigned, 'x', allowZip64=False) as target:
        with zipfile.ZipFile(UI / 'resources.apk') as resources:
            for entry in sorted(resources.infolist(), key=lambda e: (e.filename != 'AndroidManifest.xml', e.filename)):
                put(target, entry.filename, resources.read(entry), entry.compress_type)
        for dex in sorted((UI / 'dex').glob('*.dex')):
            put(target, dex.name, dex.read_bytes(), zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(OLD) as previous:
            for entry in previous.infolist():
                if not entry.filename.startswith(('assets/', 'lib/')) or entry.filename.startswith('assets/chat/'):
                    continue
                if entry.filename == NATIVE_ENTRY:
                    put(target, entry.filename, NATIVE.read_bytes(), entry.compress_type)
                    continue
                if entry.filename == 'assets/build_config.json':
                    config = json.loads(previous.read(entry))
                    config.update(ui_version='0.6.5', native_exact_prefill_block=4)
                    put(target, entry.filename, json.dumps(config, separators=(',', ':')).encode(), entry.compress_type)
                    continue
                with previous.open(entry) as source, target.open(
                        aligned_info(target, entry.filename, entry.file_size, entry.compress_type), 'w') as output:
                    shutil.copyfileobj(source, output, 4 * 1024 * 1024)
        for asset in sorted((HERE / 'android/assets/chat').glob('*')):
            put(target, f'assets/chat/{asset.name}', asset.read_bytes(), zipfile.ZIP_DEFLATED)
    run(BT / 'zipalign', '-c', '-P', '16', '4', unsigned)
    with zipfile.ZipFile(unsigned) as z:
        boundary = z.start_dir
    jar = BT / 'lib/apksigner.jar'
    classes = OUT / 'sign-classes'
    classes.mkdir(exist_ok=True)
    run('java', 'com.sun.tools.javac.Main', '-classpath', jar, '-d', classes, HERE / 'CleanSigner.java')
    run('java', '-cp', f'{classes}:{jar}', 'CleanSigner', unsigned, boundary, SECRET / 'preview.p12', SECRET / 'password')
    unsigned.rename(FINAL)
    return verify(FINAL)


def make_patch(manifest):
    segments = []
    with FINAL.open('rb') as source, zipfile.ZipFile(FINAL) as apk:
        for name in LARGE:
            entry = apk.getinfo(name)
            assert entry.compress_type == zipfile.ZIP_STORED
            source.seek(entry.header_offset + 26)
            name_bytes, extra_bytes = struct.unpack('<HH', source.read(4))
            segments.append((entry.header_offset + 30 + name_bytes + extra_bytes, entry.file_size, name))
    with zipfile.ZipFile(OUT / 'delta.zip', 'w', compression=zipfile.ZIP_DEFLATED) as delta, FINAL.open('rb') as source:
        position = 0
        order = []
        for offset, size, name in sorted(segments) + [(FINAL.stat().st_size, 0, '')]:
            piece = f'part{len(order)}.bin'
            source.seek(position)
            delta.writestr(piece, source.read(offset - position))
            order.append({'part': piece})
            if name:
                order.append({'reuse': name, 'bytes': size, 'sha256': manifest['unchanged_assets'][name]})
            position = offset + size
        delta.writestr('manifest.json', json.dumps({**manifest,'segments': order}))
    manifest['delta_bytes'] = (OUT / 'delta.zip').stat().st_size
    manifest['delta_sha256'] = sha(OUT / 'delta.zip')
    (HERE / 'reports/apk_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='unchanged_assets'}),flush=True)

if __name__ == '__main__':
    make_patch(make_apk())
