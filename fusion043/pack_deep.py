"""Create one checkpoint with the full Liquid Sense Base, Gemma blocks and tokenizer."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from locate_model import MODEL_SHA
from recover_blocks import PROFILES
from recover_gemma import REPO, REVISION, WEIGHTS_SHA

HEADER = 1024 * 1024
BLOCK_SHA = '2a2a81b765f1f8cf1eff4856aad71d554efbba36eecae01eaf1e83b5c65f3b89'


def file_sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


INSERTIONS = {
    '044': [7, 13, 19, 25],
    '045': [4, 5, 6, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 21, 22, 24, 25, 26],
}


def assemble(locator, alignment, blocks, tokenizer, stream, profile='044'):
    base = json.loads(locator.read_text())
    block_sha = file_sha(blocks)
    if profile == '044' and block_sha != BLOCK_SHA:
        raise ValueError('Pesos Gemma do experimento 044 divergentes.')
    sources = [
        ('base', Path(base['path']), base['model_offset'], base['model_bytes'], MODEL_SHA),
        ('alignment', alignment, 0, alignment.stat().st_size, file_sha(alignment)),
        ('blocks', blocks, 0, blocks.stat().st_size, block_sha),
        ('tokenizer', tokenizer, 0, tokenizer.stat().st_size, file_sha(tokenizer)),
    ]
    layers = PROFILES[profile]
    donor_parameters = len(layers) * 26_842_112
    assert alignment.stat().st_size == 4_982_784 and blocks.stat().st_size == donor_parameters * 2
    info = {'format': f'liquid-sense-gemma-deep-{profile}', 'gemma_repo': REPO,
            'gemma_revision': REVISION, 'gemma_source_sha256': WEIGHTS_SHA,
            'gemma_layers': layers, 'after_liquid_layers': INSERTIONS[profile],
            'gemma_visits_per_token': len(layers) * 2, 'liquid_visits_per_token': 56,
            'liquid_parameters': 919_659_696, 'gemma_parameters': donor_parameters,
            'interface_parameters': 2_491_392, 'total_parameters': 922_151_088 + donor_parameters,
            'new_bpe_pieces': 129}
    position = HEADER
    for name, _, _, size, digest in sources:
        info[name] = {'offset': position, 'size': size, 'sha256': digest}
        position += size
    payload = json.dumps(info, sort_keys=True, separators=(',', ':')).encode()
    prefix = f'LSMIX{profile}'.encode() + struct.pack('<I', len(payload)) + payload
    assert len(prefix) <= HEADER
    sha = hashlib.sha256()

    def write(data):
        stream.write(data)
        sha.update(data)

    write(prefix + bytes(HEADER - len(prefix)))
    for name, path, offset, size, expected in sources:
        digest = hashlib.sha256()
        with path.open('rb') as file:
            file.seek(offset)
            remaining = size
            while remaining:
                data = file.read(min(remaining, 4 * HEADER))
                if not data:
                    raise ValueError(f'Região incompleta: {name}')
                write(data)
                digest.update(data)
                remaining -= len(data)
        if digest.hexdigest() != expected:
            raise ValueError(f'SHA-256 divergente: {name}')
    return {'checkpoint_sha256': sha.hexdigest(), 'bytes': position, 'manifest': info}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('locator', 'alignment', 'blocks', 'tokenizer', 'output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--profile', choices=PROFILES, default='044')
    args = parser.parse_args()
    with args.output.open('wb') as stream:
        output = assemble(args.locator, args.alignment, args.blocks, args.tokenizer, stream, args.profile)
    print(json.dumps(output, ensure_ascii=False, indent=2))
