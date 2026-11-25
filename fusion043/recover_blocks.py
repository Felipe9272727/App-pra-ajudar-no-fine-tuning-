"""Stream complete Gemma decoder blocks in the runtime's fixed tensor order."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from urllib.request import urlopen

from recover_gemma import REPO, REVISION, WEIGHTS_BYTES, WEIGHTS_SHA

PROFILES = {
    '044': (5, 11, 17, 23),
    '045': (0, 1, 2, 4, 5, 6, 8, 9, 11, 12, 13, 15, 16, 17, 19, 20, 22, 23, 25),
}
TENSORS = (
    ('input_layernorm.weight', (1152,)),
    ('self_attn.q_proj.weight', (1024, 1152)),
    ('self_attn.k_proj.weight', (256, 1152)),
    ('self_attn.v_proj.weight', (256, 1152)),
    ('self_attn.o_proj.weight', (1152, 1024)),
    ('self_attn.q_norm.weight', (256,)),
    ('self_attn.k_norm.weight', (256,)),
    ('post_attention_layernorm.weight', (1152,)),
    ('pre_feedforward_layernorm.weight', (1152,)),
    ('mlp.gate_proj.weight', (6912, 1152)),
    ('mlp.up_proj.weight', (6912, 1152)),
    ('mlp.down_proj.weight', (1152, 6912)),
    ('post_feedforward_layernorm.weight', (1152,)),
)


def recover(output, layers):
    layout, end = {}, 0
    for layer in layers:
        for suffix, shape in TENSORS:
            size = 2 * math.prod(shape)
            layout[f'model.layers.{layer}.{suffix}'] = (end, size, shape)
            end += size
    temp = output.with_suffix('.partial')
    sha = hashlib.sha256()
    url = f'https://huggingface.co/{REPO}/resolve/{REVISION}/model.safetensors'
    with urlopen(url, timeout=75) as stream, temp.open('w+b') as target:
        def read(size):
            data = stream.read(size)
            if len(data) != size:
                raise IOError('Incomplete Gemma checkpoint')
            sha.update(data)
            return data

        length, = struct.unpack('<Q', read(8))
        assert 0 < length < 2_000_000
        header = json.loads(read(length))
        position = 0
        for name in sorted(layout, key=lambda key: header[key]['data_offsets'][0]):
            offset, size, shape = layout[name]
            spec = header[name]
            start, stop = spec['data_offsets']
            assert spec['dtype'] == 'BF16' and tuple(spec['shape']) == shape and stop - start == size
            while position < start:
                position += len(read(min(start - position, 4 << 20)))
            target.seek(offset)
            while position < stop:
                data = read(min(stop - position, 4 << 20))
                target.write(data)
                position += len(data)
            print(name, flush=True)
        while position < WEIGHTS_BYTES - length - 8:
            position += len(read(min(WEIGHTS_BYTES - length - 8 - position, 4 << 20)))
        assert stream.read(1) == b'' and sha.hexdigest() == WEIGHTS_SHA
        assert target.seek(0, 2) == end
    temp.replace(output)
    with output.open('rb') as file:
        digest = hashlib.file_digest(file, 'sha256').hexdigest()
    print(json.dumps({'sha256': digest, 'bytes': end, 'parameters': end // 2, 'layers': layers}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--profile', choices=PROFILES, default='044')
    args = parser.parse_args()
    recover(args.output, PROFILES[args.profile])
