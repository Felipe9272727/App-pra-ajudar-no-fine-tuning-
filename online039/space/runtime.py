"""Load the shipped BF16 text tensors and run the original visit-aware loop."""
import hashlib
import json
import mmap
import struct
import time
from pathlib import Path

import torch
from torch import nn
from transformers import Qwen2Tokenizer
from transformers.models.qwen3_5 import modeling_qwen3_5 as hf

from bootstrap import PACK_SHA, checked
from modeling_sensenova_loop import SenseNovaLoopConfig, SenseNovaLoopForConditionalGeneration
from native_runtime import NativeTextModel, VisitGatedMHC, extend_convolutions

CHECKPOINT_SHA = '46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'
DTYPES = {'torch.float32': torch.float32, 'torch.bfloat16': torch.bfloat16}
EOS_ID = 248044


def make_text(config):
    # Build shapes without allocating the visual weights, which this demo never loads.
    with torch.device('meta'):
        full = SenseNovaLoopForConditionalGeneration(config)
        text = full.model.language_model
        text.__class__ = NativeTextModel
        for i in range(4, 28):
            layer = text.layers[i]
            layer.__class__ = VisitGatedMHC
            layer.native_visit_gain = nn.Parameter(torch.empty(2, dtype=torch.float32), requires_grad=False)
            layer._native_window = 256 if i in (7, 15, 27) else 0
        extend_convolutions(full)
    with torch.device('cpu'):
        text.rotary_emb = hf.Qwen3_5TextRotaryEmbedding(text.config)
    return text


def load_text_weights(text, pack):
    checked(pack, PACK_SHA)
    with pack.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        if data[:8] != b'LSENSE01':
            raise ValueError('Formato de pesos inesperado')
        header_size = struct.unpack('<Q', data[8:16])[0]
        manifest = json.loads(data[16:16 + header_size])
        tensors = manifest['tensors']
        plan = manifest['execution_plan']
        if (manifest['quantization'] != 'bf16' or
                manifest['source_checkpoint_sha256'] != CHECKPOINT_SHA or
                len(tensors) != 546 or len(text.layers) != 32 or len(plan) != 56 or
                list(text._loop_plan) != plan):
            raise ValueError('Checkpoint ou plano de loop inesperado')
        expected = dict(text.named_parameters())
        if set(expected) != set(tensors):
            raise ValueError('O pacote não corresponde aos tensores do motor')
        aliases = {}
        hashes = {}
        for name, spec in tensors.items():
            shape = tuple(spec['shape'])
            if shape != tuple(expected[name].shape):
                raise ValueError(f'Formato inesperado para o tensor {name}')
            dtype = DTYPES[spec['source_dtype']]
            kind = spec['kind']
            offset, size = spec['offset'], spec['bytes']
            key = (offset, size, shape, kind, dtype)
            if key not in aliases:
                if kind == 'zero':
                    tensor = torch.zeros(shape, dtype=dtype)
                elif kind in ('f32', 'bf16'):
                    raw = bytearray(data[offset:offset + size])
                    tensor = torch.frombuffer(raw, dtype=dtype).reshape(shape)
                else:
                    raise ValueError(f'Codificação de tensor inesperada: {kind}')
                hashes[key] = hashlib.sha256(memoryview(tensor.view(torch.uint8).numpy()).cast('B')).hexdigest()
                aliases[key] = nn.Parameter(tensor, requires_grad=False)
            if hashes[key] != spec['source_sha256']:
                raise ValueError(f'SHA256 divergente para o tensor {name}')
            module, _, parameter = name.rpartition('.')
            text.get_submodule(module)._parameters[parameter] = aliases[key]
    return manifest


class Runtime:
    def __init__(self, folder, device='cpu'):
        folder = Path(folder)
        config = SenseNovaLoopConfig.from_dict(json.loads((folder / 'config.json').read_text()))
        config._attn_implementation = 'eager'
        config.text_config._attn_implementation = 'eager'
        text = make_text(config)
        self.manifest = load_text_weights(text, folder / 'model.lsp')
        self.audit = {name: spec['source_sha256'] for name, spec in self.manifest['tensors'].items()}
        self.text = text.eval().requires_grad_(False).to(device)
        self.tok = Qwen2Tokenizer.from_pretrained(folder, local_files_only=True)
        self.identity = json.loads((folder / 'identity.json').read_text())['system_message']
        self.device = device

    @torch.inference_mode()
    def generate(self, messages, budget=128, thinking=False):
        if not 1 <= budget <= 512:
            raise ValueError('Escolha um limite entre 1 e 512 tokens.')
        if not messages or any(m.get('role') not in ('user', 'assistant') or not isinstance(m.get('content'), str)
                               for m in messages):
            raise ValueError('Mensagens inválidas.')
        prefix = self.tok.apply_chat_template(
            [{'role': 'system', 'content': self.identity}, *messages],
            tokenize=True, add_generation_prompt=True, enable_thinking=thinking, return_dict=False,
        )
        if len(prefix) > 2048:
            raise ValueError('O protótipo aceita até 2048 tokens de entrada.')
        ids = torch.tensor([prefix], device=self.device)
        cache = None
        tokens = []
        started = time.perf_counter()
        first = None
        for _ in range(budget):
            output = self.text(input_ids=ids, past_key_values=cache, use_cache=True)
            cache = output.past_key_values
            logits = nn.functional.linear(output.last_hidden_state[:, -1], self.text.embed_tokens.weight).float()
            next_id = logits.argmax(-1)
            token = int(next_id.item())
            if first is None:
                first = time.perf_counter() - started
            tokens.append(token)
            if token == EOS_ID:
                break
            ids = next_id.view(1, 1)
        seconds = time.perf_counter() - started
        return {
            'text': self.tok.decode(tokens, skip_special_tokens=True),
            'tokens': tokens,
            'seconds': seconds,
            'first_token_seconds': first,
            'decode_tokens_per_second': (len(tokens) - 1) / max(1e-9, seconds - first) if len(tokens) > 1 else None,
            'ended_eos': tokens[-1] == EOS_ID,
            'device': str(self.text.embed_tokens.weight.device),
            'physical_layers': len(self.text.layers),
            'execution_visits': len(self.text._loop_plan),
            'weights_SHA256': PACK_SHA,
            'prototype': True,
        }
