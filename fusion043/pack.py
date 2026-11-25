"""Portable little-endian BF16 format for the research checkpoint overlay."""
import json
import struct
from pathlib import Path

import numpy as np
import torch

MAGIC = b'LSFUSE01'
LIQUID = 1024
GEMMA = 1152
ROWS = 248320
CHANNELS = 512
RANK = 32
BASE = '46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'


def shapes(n):
    return {
        'input': (GEMMA, LIQUID), 'gate': (CHANNELS, GEMMA), 'up': (CHANNELS, GEMMA),
        'down': (GEMMA, CHANNELS), 'pre': (GEMMA,), 'post': (GEMMA,),
        'feature': (RANK, GEMMA), 'output': (LIQUID, RANK), 'lexicon': (n, LIQUID),
    }


def tensor_bits(t):
    return t.detach().to(torch.bfloat16).contiguous().view(torch.uint16).numpy().astype('<u2', copy=False)


def write_pack(filename, meta, tensors):
    layout = shapes(len(meta['tokens']))
    prefix = json.dumps(meta,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    with Path(filename).open('wb') as file:
        file.write(MAGIC + struct.pack('<I',len(prefix)) + prefix)
        for name, shape in layout.items():
            data = tensor_bits(tensors[name])
            assert data.shape == shape
            file.write(data.tobytes())


def read_pack(filename):
    with Path(filename).open('rb') as file:
        assert file.read(8) == MAGIC
        meta = json.loads(file.read(struct.unpack('<I',file.read(4))[0]))
        tensors = {}
        for name, shape in shapes(len(meta['tokens'])).items():
            count = int(np.prod(shape))
            values = np.frombuffer(file.read(count*2), dtype='<u2').copy().reshape(shape)
            tensors[name] = torch.from_numpy(values).view(torch.bfloat16).float()
        assert file.read(1) == b''
    return meta, tensors


def embeddings(locator):
    loc = json.loads(Path(locator).read_text())
    with Path(loc['path']).open('rb') as file:
        file.seek(loc['model_offset'])
        assert file.read(8) == b'LSENSE01'
        header = json.loads(file.read(struct.unpack('<Q',file.read(8))[0]))
    assert header['source_checkpoint_sha256'] == BASE
    spec = header['tensors']['embed_tokens.weight']
    assert spec['kind'] == 'bf16' and spec['shape'] == [ROWS, LIQUID]
    data = np.memmap(loc['path'], mode='r', dtype='<u2', offset=loc['model_offset']+spec['offset'], shape=(ROWS,LIQUID))
    return data


def rows(data, ids):
    return torch.from_numpy(np.asarray(data[ids]).copy()).view(torch.bfloat16).float()
