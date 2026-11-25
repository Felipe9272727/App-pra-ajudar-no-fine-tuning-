"""Verify the published Liquid Sense text pack and return its mmap region."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

MODEL = 'assets/model.lsp'
TOKENIZER = 'assets/tokenizer.json'
MODEL_SHA = '6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288'
TOKENIZER_SHA = '5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42'


def locate(path, tokenizer=None):
    with path.open('rb') as file:
        if file.read(8) == b'LSENSE01':
            if tokenizer is not None:
                raise ValueError('Use o APK para extrair o tokenizer original.')
            file.seek(0)
            offset, size = 0, path.stat().st_size
            digest = hashlib.file_digest(file, 'sha256').hexdigest()
        else:
            with zipfile.ZipFile(path) as archive:
                entry = archive.getinfo(MODEL)
                if entry.compress_type != zipfile.ZIP_STORED:
                    raise ValueError('Extraia assets/model.lsp e indique o arquivo extraído.')
                file.seek(entry.header_offset)
                header = file.read(30)
                if not header.startswith(b'PK\x03\x04'):
                    raise ValueError('Cabeçalho ZIP incompatível.')
                filename, extra = struct.unpack_from('<HH', header, 26)
                offset = entry.header_offset + 30 + filename + extra
                size = entry.file_size
                with archive.open(entry) as source:
                    digest = hashlib.file_digest(source, 'sha256').hexdigest()
                if tokenizer is not None:
                    original = archive.read(TOKENIZER)
                    if hashlib.sha256(original).hexdigest() != TOKENIZER_SHA:
                        raise ValueError('Tokenizer original divergente.')
    if digest != MODEL_SHA:
        raise ValueError('O SHA-256 dos pesos da Base Liquid Sense diverge.')
    if tokenizer is not None:
        tokenizer.write_bytes(original)
    return {'path': str(path.resolve()), 'model_offset': offset,
            'model_bytes': size, 'model_sha256': digest}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('--tokenizer', type=Path)
    args = parser.parse_args()
    print(json.dumps(locate(args.base, args.tokenizer), indent=2))
