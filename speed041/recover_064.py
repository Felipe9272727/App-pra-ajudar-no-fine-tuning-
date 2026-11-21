"""Rebuild the exact 0.6.4 APK from its public, signed compact updater."""

import argparse
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

from locate import BASES

PREVIOUS_UPDATER_SHA = 'ab626884c1e7c49bdd44001f78c37317167afedc45a259602672af72fd49e24b'
PREVIOUS_APK_SHA = 'd005159c879f86d1fcf007f9660ce6a56d008be57eafbda0946c03e0272ee746'


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def recover(base, updater, output):
    if digest(base) not in BASES or digest(updater) != PREVIOUS_UPDATER_SHA:
        raise ValueError('Arquivos de origem divergentes')
    with zipfile.ZipFile(updater) as helper:
        raw_delta = helper.read('assets/delta.zip')
    with zipfile.ZipFile(base) as original, zipfile.ZipFile(io.BytesIO(raw_delta)) as delta:
        spec = json.loads(delta.read('manifest.json'))
        if spec['sha256'] != PREVIOUS_APK_SHA:
            raise ValueError('Manifesto de atualização divergente')
        with output.open('xb') as new:
            for item in spec['segments']:
                source = original if 'reuse' in item else delta
                name = item.get('reuse') or item['part']
                with source.open(name) as data:
                    shutil.copyfileobj(data, new, 4 * 1024 * 1024)
    if output.stat().st_size != spec['bytes'] or digest(output) != PREVIOUS_APK_SHA:
        raise ValueError('APK 0.6.4 reconstruído com hash incorreto')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('v063', type=Path)
    parser.add_argument('updater', type=Path)
    parser.add_argument('v064', type=Path)
    args = parser.parse_args()
    recover(args.v063, args.updater, args.v064)
