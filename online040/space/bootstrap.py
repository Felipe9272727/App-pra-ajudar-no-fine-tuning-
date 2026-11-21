"""Recover the text pack from the project's pinned public release."""
import hashlib
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

PACK_SHA = '6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288'
ZIP_SHA = '52966dccfc9ec1dd6f4eaeabadaa3615c31e286034d84c04a74690042724f307'
APK_NAME = 'LiquidSense-0.6.3-install-preview.apk'
URL = ('https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/'
       'liquid-sense-0.6.3-verified035/LiquidSense-0.6.3-verificado.zip')
# Byte offset and length of the stored asset in this exact, hash-checked APK.
PACK_OFFSET = 15_503_448
PACK_BYTES = 1_599_290_240
BUFFER_BYTES = 4 * 1024 * 1024


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def checked(path, expected):
    if sha(path) != expected:
        raise ValueError(f'SHA256 divergente: {path.name}')


def download(url, destination):
    with urllib.request.urlopen(url, timeout=90) as response, destination.open('xb') as output:
        shutil.copyfileobj(response, output, BUFFER_BYTES)


def recover_pack(archive, destination):
    checked(archive, ZIP_SHA)
    with zipfile.ZipFile(archive) as outer, outer.open(APK_NAME) as apk:
        if apk.seek(PACK_OFFSET) != PACK_OFFSET or apk.read(8) != b'LSENSE01':
            raise ValueError('Cabeçalho do pacote de pesos ausente')
        apk.seek(PACK_OFFSET)
        remaining = PACK_BYTES
        with destination.open('xb') as output:
            while remaining:
                chunk = apk.read(min(remaining, BUFFER_BYTES))
                if not chunk:
                    raise ValueError('Pacote de pesos truncado')
                output.write(chunk)
                remaining -= len(chunk)
    checked(destination, PACK_SHA)


def prepare(folder, archive=None):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).parent
    manifest = json.loads((source / 'assets_manifest.json').read_text())
    with tempfile.TemporaryDirectory(prefix='liquid-startup-', dir=folder) as workdir:
        work = Path(workdir)
        pack = folder / 'model.lsp'
        if not pack.exists():
            if archive is None:
                archive = work / 'source.zip'
                download(URL, archive)
            recover_pack(Path(archive), work / pack.name)
            (work / pack.name).replace(pack)
        else:
            checked(pack, PACK_SHA)
        for name, row in manifest.items():
            destination = folder / name
            if destination.exists():
                checked(destination, row['sha256'])
                continue
            temporary = work / name
            if 'url' in row:
                download(row['url'], temporary)
            else:
                shutil.copyfile(source / 'seed' / name, temporary)
            checked(temporary, row['sha256'])
            temporary.replace(destination)
    return folder
