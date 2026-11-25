"""Verify the whole pinned Gemma 3 1B BF16 checkpoint while retaining selected tensors."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from urllib.request import urlopen

REPO = 'unsloth/gemma-3-1b-it'
REVISION = '5b11413a10db4e486ef16a20101fd028f8f2499c'
WEIGHTS_SHA = '3d4ef8d71c14db7e448a09ebe891cfb6bf32c57a9b44499ae0d1c098e48516b6'
TOKENIZER_SHA = '4667f2089529e8e7657cfb6d1c19910ae71ff5f28aa7ab2ff2763330affad795'
WEIGHTS_BYTES = 1999811208
TENSORS = {
    'model.embed_tokens.weight': (262144, 1152),
    'model.layers.25.mlp.gate_proj.weight': (6912, 1152),
    'model.layers.25.mlp.up_proj.weight': (6912, 1152),
    'model.layers.25.mlp.down_proj.weight': (1152, 6912),
    'model.layers.25.pre_feedforward_layernorm.weight': (1152,),
    'model.layers.25.post_feedforward_layernorm.weight': (1152,),
}


def recover(folder):
    folder.mkdir(parents=True, exist_ok=True)
    base = f'https://huggingface.co/{REPO}/resolve/{REVISION}/'
    for filename in ('config.json', 'tokenizer.json'):
        with urlopen(base + filename, timeout=45) as remote:
            data = remote.read()
        if filename == 'tokenizer.json':
            assert hashlib.sha256(data).hexdigest() == TOKENIZER_SHA
        (folder/filename).write_bytes(data)

    header_hash = hashlib.sha256()
    entries = {}
    with urlopen(base + 'model.safetensors', timeout=75) as source:
        def read(size):
            part = source.read(size)
            if len(part) != size:
                raise IOError('Truncated Gemma checkpoint')
            header_hash.update(part)
            return part

        length, = struct.unpack('<Q', read(8))
        assert 0 < length < 2_000_000
        specs = json.loads(read(length))
        position = 0

        def transfer(length, output=None, tensor_hash=None):
            while length:
                part = read(min(length, 4*1024*1024))
                if output is not None:
                    output.write(part)
                    tensor_hash.update(part)
                length -= len(part)

        for name, shape in sorted(TENSORS.items(), key=lambda item: specs[item[0]]['data_offsets'][0]):
            spec = specs[name]
            begin, end = spec['data_offsets']
            count = 1
            for dimension in shape:
                count *= dimension
            assert spec['dtype'] == 'BF16' and tuple(spec['shape']) == shape and end-begin == count*2
            transfer(begin-position)
            dest = folder/(name+'.bf16')
            tensor_hash = hashlib.sha256()
            with dest.open('wb') as output:
                transfer(end-begin, output, tensor_hash)
            position = end
            entries[name] = {'shape': shape, 'bytes': count*2, 'sha256': tensor_hash.hexdigest()}
            print('Retained', name, shape, flush=True)
        transfer(WEIGHTS_BYTES-8-length-position)
        assert source.read(1) == b''
    assert header_hash.hexdigest() == WEIGHTS_SHA
    (folder/'verified.json').write_text(json.dumps({'repo': REPO, 'revision': REVISION,
        'weights_sha256': WEIGHTS_SHA, 'tokenizer_sha256': TOKENIZER_SHA, 'tensors': entries},indent=2)+'\n')
    print('Complete Gemma checkpoint SHA-256 verified', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('output', type=Path)
    recover(p.parse_args().output)
