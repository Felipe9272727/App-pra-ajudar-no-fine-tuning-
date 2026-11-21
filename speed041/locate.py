"""Locate and verify the exact text and trained patch in a signed app archive."""

import argparse
import hashlib
import json
import struct
import zipfile
from pathlib import Path


BASES = {
    '4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10',
    'd005159c879f86d1fcf007f9660ce6a56d008be57eafbda0946c03e0272ee746',
}
ASSETS = {
    'model': ('assets/model.lsp', '6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288'),
    'patch': ('assets/epoch02.lspatch', '0f19e758cbad61f86ca144c685994d1d6710b85b36d64e2a8be98731fe497310'),
}


def locate(apk):
    with apk.open('rb') as f:
        sha256 = hashlib.file_digest(f, 'sha256').hexdigest()
        if sha256 not in BASES:
            raise ValueError('APK original divergente')
        info = {'path': str(apk.resolve()), 'apk_sha256': sha256}
        with zipfile.ZipFile(apk) as archive:
            for key, (name, digest) in ASSETS.items():
                entry = archive.getinfo(name)
                if entry.compress_type != zipfile.ZIP_STORED:
                    raise ValueError(f'Asset precisa estar sem compressão: {name}')
                with archive.open(entry) as source:
                    if hashlib.file_digest(source, 'sha256').hexdigest() != digest:
                        raise ValueError(f'Asset divergente: {name}')
                f.seek(entry.header_offset + 26)
                n, extra = struct.unpack('<HH', f.read(4))
                info[f'{key}_offset'] = entry.header_offset + 30 + n + extra
                info[f'{key}_bytes'] = entry.file_size
                info[f'{key}_sha256'] = digest
    return info


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('apk', type=Path)
    args = parser.parse_args()
    print(json.dumps(locate(args.apk), indent=2))
