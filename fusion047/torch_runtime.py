"""Torch execution of the published 045 tensor layout and 046-format readout."""
import hashlib
import json
import mmap
from operator import index
from pathlib import Path
import struct
import time

import numpy as np
import torch
from torch.nn import functional as F
from tokenizers import Tokenizer

PARENT = 'e6e4528057543f0bdf35305c87b79197c639f2d77ddfcf140745a62f4441703c'
PLAN = tuple(range(4)) + tuple(range(4, 28)) * 2 + tuple(range(28, 32))
GEMMA_SHAPES = (
    (1152,), (1024, 1152), (256, 1152), (256, 1152), (1152, 1024),
    (256,), (256,), (1152,), (1152,), (6912, 1152), (6912, 1152),
    (1152, 6912), (1152,),
)
SYSTEM = 'You are a helpful assistant.'
MAX_RESPONSE_TOKENS = 4096
MAX_REASONING_TOKENS = 2048
MAX_CONTEXT_TOKENS = 16384


def generation_budget(prompt_tokens, closing_tokens, response_tokens, reasoning_tokens, context_tokens):
    try:
        requested_response = index(response_tokens)
        requested_reasoning = index(reasoning_tokens)
        context_limit = min(index(context_tokens), MAX_CONTEXT_TOKENS)
    except TypeError as error:
        raise ValueError('Informe os limites de geração em números inteiros.') from error
    available = context_limit - prompt_tokens - closing_tokens
    if available < 1:
        raise ValueError(f'A pergunta ocupa {prompt_tokens} tokens do contexto de {context_limit}. Encurte a pergunta.')
    response = min(max(requested_response, 1), MAX_RESPONSE_TOKENS, available)
    reasoning = min(max(requested_reasoning, 0), MAX_REASONING_TOKENS, available - response)
    capacity = prompt_tokens + closing_tokens + response + reasoning
    return response, reasoning, capacity


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def bf(x):
    return x.to(torch.bfloat16).float()


def rms(x, w):
    return bf(x * (x.square().mean(dim=-1, keepdim=True) + 1e-6).rsqrt() * (1 + w))


def gates(bias):
    pre = bf(bias[:2].sigmoid())
    post = 2 * bias[2:4].sigmoid()
    mix = bias[4:].reshape(2, 2)
    for _ in range(20):
        mix = mix - mix.logsumexp(1, keepdim=True)
        mix = mix - mix.logsumexp(0, keepdim=True)
    return pre, post, bf(mix.exp())


def route(x, pre):
    return bf(x[:, 0]*pre[0] + x[:, 1]*pre[1])


def merge(x, branch, post, mix, gain):
    mixed = bf(x[:, 0, None]*mix[:, 0, None] + x[:, 1, None]*mix[:, 1, None])
    return bf(mixed + bf(branch[:, None]*bf(post*gain)[:, None]))


class Session:
    def __init__(self, capacity, device):
        self.capacity = capacity
        self.device = device
        self.position = 0
        self.recurrent = {}
        self.kv = {}

    def attention(self, key, q, k, v, positions, window, liquid):
        steps, heads, width = q.shape
        kv_heads = k.shape[1]
        if key not in self.kv:
            shape = (self.capacity, kv_heads, width)
            self.kv[key] = tuple(torch.empty(shape, device=self.device, dtype=torch.bfloat16) for _ in range(2))
        keys, values = self.kv[key]
        first = self.position
        end = first + steps
        keys[first:end] = k
        values[first:end] = v
        start = max(0, first-window+1) if window else 0
        query = q.reshape(steps, kv_heads, heads//kv_heads, width).permute(1, 2, 0, 3)
        K = keys[start:end].float().permute(1, 2, 0)[:, None]
        V = values[start:end].float().permute(1, 0, 2)[:, None]
        scores = query @ K
        scores = bf(bf(scores) * 0.0625) if liquid else scores * 0.0625
        past = torch.arange(start, end, device=self.device)
        mask = past <= positions[:, None]
        if window:
            mask = mask & (past > positions[:, None]-window)
        scores.masked_fill_(~mask, -torch.inf)
        result = bf(bf(scores.softmax(dim=-1)) @ V)
        return result.permute(2, 0, 1, 3).reshape(steps, heads, width)


class LiquidSenseTorch:
    @torch.inference_mode()
    def __init__(self, checkpoint, adapter, expected_adapter, device='cuda', *,
                 verified_parent=False, identity=None, identity_sha=None):
        self.device = torch.device(device)
        if self.device.type == 'cuda' and not torch.cuda.is_available():
            raise RuntimeError('Ative uma GPU T4 no ambiente de execução do Colab.')
        self.cuda = self.device.type == 'cuda'
        self.precision = torch.float16 if self.cuda else torch.bfloat16
        if self.cuda:
            torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction = False
        if not verified_parent and digest(checkpoint) != PARENT:
            raise ValueError('SHA-256 inválido para o checkpoint híbrido.')
        if digest(adapter) != expected_adapter:
            raise ValueError('SHA-256 inválido para a correção.')
        with Path(checkpoint).open('rb') as file:
            self.source = mmap.mmap(file.fileno(), 0, access=mmap.ACCESS_COPY)
        raw = self.source
        if raw[:8] != b'LSMIX045':
            raise ValueError('Formato do checkpoint inválido.')
        length = struct.unpack_from('<I', raw, 8)[0]
        doc = json.loads(raw[12:12+length])
        offset = doc['base']['offset']
        length = struct.unpack_from('<Q', raw, offset+8)[0]
        base = json.loads(raw[offset+16:offset+16+length])
        self.plan = tuple(base['execution_plan'])
        if self.plan != PLAN or len(doc['gemma_layers']) != 19:
            raise ValueError('Plano de execução incompatível.')

        self.weights = {}
        for name, spec in base['tensors'].items():
            if spec['kind'] == 'zero':
                continue
            dtype = torch.float32 if spec['kind'] == 'f32' else torch.bfloat16
            if spec['kind'] not in ('f32', 'bf16'):
                raise ValueError(f'Formato de tensor não suportado em {name}.')
            self.weights[name] = self.tensor(raw, dtype, offset+spec['offset'], spec['shape'])
        self.routing = {}
        for layer in range(4, 28):
            for name in ('mhc_attn', 'mhc_ffn'):
                key = f'layers.{layer}.{name}'
                if base['tensors'][key+'.weight']['kind'] != 'zero':
                    raise ValueError('Router dinâmico incompatível com este checkpoint.')
                # Compute each fixed router once and retain it on the selected device.
                self.routing[key] = gates(self.weights[key+'.bias'])

        offset = doc['alignment']['offset']
        self.align_in = self.tensor(raw, torch.bfloat16, offset, (1152, 1024))
        self.align_out = self.tensor(raw, torch.bfloat16, offset+2*1152*1024, (1024, 1152))
        lexicon = self.tensor(raw, torch.bfloat16, offset+4*1152*1024, (129, 1024))
        embedding = self.weights['embed_tokens.weight'][:248199].clone()
        embedding[248070:] = lexicon
        self.weights['embed_tokens.weight'] = embedding
        self.lexical_bias = torch.zeros(248199, device=self.device)
        self.lexical_bias[248070:] = -.75
        self.gemma = {}
        offset = doc['blocks']['offset']
        for source, layer in zip(doc['gemma_layers'], doc['after_liquid_layers']):
            values = []
            for shape in GEMMA_SHAPES:
                values.append(self.tensor(raw, torch.bfloat16, offset, shape))
                offset += 2 * values[-1].numel()
            self.gemma[layer] = (source, values)
        if offset != doc['blocks']['offset'] + doc['blocks']['size']:
            raise ValueError('O tamanho dos blocos Gemma diverge.')

        region = doc['tokenizer']
        self.tokenizer = Tokenizer.from_buffer(raw[region['offset']:region['offset']+region['size']])
        if self.tokenizer.get_vocab_size() != len(embedding):
            raise ValueError('O vocabulário e o embedding divergem.')
        raw_adapter = bytearray(Path(adapter).read_bytes())
        length = struct.unpack_from('<I', raw_adapter, 8)[0]
        config = json.loads(raw_adapter[12:12+length])
        if raw_adapter[:8] != b'LSCAL046' or config['parent'] != PARENT or config['rank'] != 48:
            raise ValueError('Correção incompatível.')
        offset = 12 + length
        self.read_in = self.tensor(raw_adapter, torch.bfloat16, offset, (48, 1024))
        self.read_out = self.tensor(raw_adapter, torch.bfloat16, offset+2*48*1024, (1024, 48))
        self.bound = config['bound']
        self.gains = {
            layer: torch.tensor([config['gains'][i], config['gains'][i+19]], device=self.device)
            for i,layer in enumerate(doc['after_liquid_layers'])
        }
        self.frequencies = {
            (n, theta): 1 / (theta**(torch.arange(n, device=self.device, dtype=torch.float32)/n))
            for n,theta in [(32, 10_000_000), (128, 1_000_000), (128, 10_000)]
        }
        self.identity = None if identity is None else self.load_identity(identity, identity_sha, expected_adapter)

    def load_identity(self, path, expected_sha, adapter):
        if digest(path) != expected_sha:
            raise ValueError('SHA-256 inválido para os pesos de identidade.')
        with np.load(path, allow_pickle=False) as data:
            metadata = json.loads(data['metadata'].item())
            ids, matrix, gate = data['ids'], data['matrix'], data['gate']
            threshold = float(data['threshold'].item())
        if metadata != {'format':'liquid-sense-identity-head-v1','parent_adapter':adapter}:
            raise ValueError('Pesos de identidade de outra versão.')
        if (ids.ndim != 1 or len(ids)==0 or len(ids)>248199 or np.any(ids[1:]<=ids[:-1])
                or ids[0]<0 or ids[-1]>=248199 or matrix.shape!=(len(ids),1025)
                or matrix.dtype!=np.uint16 or gate.shape!=(1025,) or gate.dtype!=np.uint16
                or not np.isfinite(threshold)):
            raise ValueError('Formato inválido dos pesos de identidade.')
        gate = torch.from_numpy(gate.copy()).view(torch.bfloat16).to(device=self.device, dtype=torch.float32)
        matrix = torch.from_numpy(matrix.copy()).view(torch.bfloat16).to(device=self.device, dtype=torch.float32)
        return (torch.from_numpy(ids.astype(np.int64)).to(self.device), matrix, gate, threshold)

    def identity_features(self, hidden):
        x = F.normalize(hidden, dim=-1, eps=1e-6)
        return torch.cat((x, x.new_full((len(x),1), .25)), dim=1)

    def tensor(self, source, dtype, offset, shape):
        size = 1
        for dim in shape:
            size *= dim
        x = torch.frombuffer(source, dtype=dtype, count=size, offset=offset).reshape(shape)
        target = self.precision if len(shape) == 2 else torch.float32
        return x.to(device=self.device, dtype=target)

    def project(self, w, x):
        if self.cuda:
            # CUDA accumulates FP16 products in FP32 on T4. Restore the BF16 boundaries used by Rust.
            return bf(torch.mm(x.to(self.precision), w.T, out_dtype=torch.float32))
        return F.linear(x.to(self.precision), w).float()

    def mv(self, prefix, suffix, x):
        return self.project(self.weights[f'{prefix}.{suffix}.weight'], x)

    def rotate(self, x, positions, liquid=False, global_=False):
        n, theta = (32, 10_000_000) if liquid else (128, 1_000_000 if global_ else 10_000)
        angle = positions[:, None, None] * self.frequencies[n, theta]
        c, s = angle.cos(), angle.sin()
        a, b = x[..., :n], x[..., n:2*n]
        if liquid:
            c, s = bf(c), bf(s)
            return torch.cat((bf(bf(a*c)+bf(-b*s)), bf(bf(b*c)+bf(a*s)), x[...,2*n:]), dim=-1)
        return torch.cat((bf(a*c-b*s), bf(b*c+a*s)), dim=-1)

    def liquid_attention(self, layer, slot, x, pos, session):
        p = f'layers.{layer}.self_attn'
        steps = len(x)
        q, gate = self.mv(p, 'q_proj', x).reshape(steps, 8, 512).split(256, dim=-1)
        k = self.mv(p, 'k_proj', x).reshape(steps, 2, 256)
        v = self.mv(p, 'v_proj', x).reshape(steps, 2, 256)
        q = self.rotate(rms(q, self.weights[p+'.q_norm.weight']), pos, liquid=True)
        k = self.rotate(rms(k, self.weights[p+'.k_norm.weight']), pos, liquid=True)
        y = session.attention(slot, q, k, v, pos, 256 if layer in (7,15,27) else 0, liquid=True)
        return self.mv(p, 'o_proj', bf(y*bf(gate.sigmoid())).flatten(1))

    def delta(self, layer, slot, x, session):
        p = f'layers.{layer}.linear_attn'
        w = self.weights
        qkv = self.mv(p, 'in_proj_qkv', x)
        z = self.mv(p, 'in_proj_z', x).reshape(-1, 16, 128)
        decay = (-w[p+'.A_log'].exp()*F.softplus(self.mv(p, 'in_proj_a', x)+w[p+'.dt_bias'])).exp()
        beta = bf(self.mv(p, 'in_proj_b', x).sigmoid())
        if slot not in session.recurrent:
            session.recurrent[slot] = (
                torch.zeros(6, 6144, device=self.device),
                torch.zeros(16, 128, 128, device=self.device),
            )
        conv_history, state = session.recurrent[slot]
        conv = w[p+'.conv1d.weight'].reshape(6144, 7)
        all_input = torch.cat((conv_history, qkv))
        filtered = bf(F.silu(bf((all_input.unfold(0, 7, 1)*conv).sum(-1))))
        queries, keys, values = filtered.reshape(-1, 3, 16, 128).unbind(1)
        queries = queries * (queries.square().sum(-1, keepdim=True)+1e-6).rsqrt() / (128**.5)
        keys = keys * (keys.square().sum(-1, keepdim=True)+1e-6).rsqrt()
        output = []
        for q, k, v, g, b in zip(queries, keys, values, decay, beta):
            state = state * g[:, None, None]
            first = torch.bmm(k[:, None], state).squeeze(1)
            state = state + k[:, :, None]*((v-first)*b[:, None])[:, None]
            output.append(bf(torch.bmm(q[:, None], state).squeeze(1)))
        session.recurrent[slot] = all_input[-6:].clone(), state
        y = torch.stack(output)
        y = bf(y * (y.square().mean(-1, keepdim=True)+1e-6).rsqrt())
        y = bf(bf(y*w[p+'.norm.weight'])*F.silu(z))
        return self.mv(p, 'out_proj', y.flatten(1))

    def gemma_block(self, layer, visit, residual, pos, session):
        source, weights = self.gemma[layer]
        pre, qw, kw, vw, ow, qn, kn, post, preff, gate, up, down, postff = weights
        shared = bf((residual[:, 0]+residual[:, 1])*.5)
        x = self.project(self.align_in, shared)
        normalized = rms(x, pre)
        global_ = (source+1)%6 == 0
        q = self.rotate(rms(self.project(qw, normalized).reshape(-1,4,256), qn), pos, global_=global_)
        k = self.rotate(rms(self.project(kw, normalized).reshape(-1,1,256), kn), pos, global_=global_)
        v = self.project(vw, normalized).reshape(-1,1,256)
        key = ('gemma', layer, visit)
        y = session.attention(key, q, k, v, pos, 0 if global_ else 512, liquid=False)
        h = bf(x + rms(self.project(ow, y.flatten(1)), post))
        normalized = rms(h, preff)
        activated = bf(F.gelu(self.project(gate, normalized), approximate='tanh'))
        out = self.project(down, bf(activated*self.project(up,normalized)))
        aligned = self.project(self.align_out, bf(h+rms(out,postff))-x).tanh()
        scale = self.gains[layer][visit] * shared.square().mean(-1, keepdim=True).sqrt()
        return bf(residual + (scale*aligned)[:, None])

    @torch.inference_mode()
    def advance(self, ids, session):
        count = len(ids)
        positions = torch.arange(session.position, session.position+count, device=self.device)
        h = self.weights['embed_tokens.weight'][ids].float()
        visits = [0]*32
        for slot,layer in enumerate(self.plan):
            visit = visits[layer]
            visits[layer] += 1
            prefix = f'layers.{layer}'
            routed = 4 <= layer < 28
            if layer == 4:
                h = torch.stack((h,h),dim=1)
            if routed:
                gain = self.weights[prefix+'.native_visit_gain'][visit]
                pre, post, mix = self.routing[prefix+'.mhc_attn']
                branch = route(h, pre)
            else:
                branch = h
            x = rms(branch, self.weights[prefix+'.input_layernorm.weight'])
            y = self.liquid_attention(layer, slot, x, positions, session) if layer%4==3 else self.delta(layer, slot, x, session)
            if routed:
                h = merge(h, y, post, mix, gain)
                pre, post, mix = self.routing[prefix+'.mhc_ffn']
                branch = route(h, pre)
            else:
                h = bf(h+y)
                branch = h
            x = rms(branch, self.weights[prefix+'.post_attention_layernorm.weight'])
            gate = bf(F.silu(self.mv(prefix+'.mlp', 'gate_proj', x)))
            y = self.mv(prefix+'.mlp', 'down_proj', bf(gate*self.mv(prefix+'.mlp','up_proj',x)))
            if routed:
                h = merge(h, y, post, mix, gain)
                if layer in self.gemma:
                    h = self.gemma_block(layer, visit, h, positions, session)
                if layer == 27:
                    h = bf((h[:,0]+h[:,1])*.5)
            else:
                h = bf(h+y)
        session.position += count
        return rms(h[-1:], self.weights['norm.weight'])

    @torch.inference_mode()
    def generate(self, prompt, thinking=False, reasoning_tokens=192, response_tokens=128, context_tokens=MAX_CONTEXT_TOKENS):
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError('Escreva uma pergunta.')
        opening = '<think>\n' if thinking else '<think>\n\n</think>\n\n'
        formatted = (f'<|im_start|>system\n{SYSTEM}<|im_end|>\n<|im_start|>user\n'
                     f'{prompt.strip()}<|im_end|>\n<|im_start|>assistant\n{opening}')
        ids = self.tokenizer.encode(formatted, add_special_tokens=False).ids
        closing = self.tokenizer.encode('</think>\n\n', add_special_tokens=False).ids if thinking else []
        response_tokens, reasoning_tokens, capacity = generation_budget(
            len(ids), len(closing), response_tokens, reasoning_tokens if thinking else 0, context_tokens,
        )
        session = Session(capacity, self.device)
        if self.cuda:
            torch.cuda.synchronize()
        start = time.perf_counter()
        input_ids = torch.tensor(ids, dtype=torch.long, device=self.device)
        for group in input_ids.split(32):
            hidden = self.advance(group, session)
        identity_active = False
        if self.identity is not None:
            identity_ids, rows, gate, threshold = self.identity
            identity_active = float(self.identity_features(hidden)[0] @ gate) >= threshold
        first_token = None
        generated, reasoning_count, response_count = [], 0, 0
        finished_thinking = not thinking
        stop_reason = 'length'
        while response_count < response_tokens:
            at_limit = not finished_thinking and reasoning_count >= reasoning_tokens
            if not at_limit:
                correction = self.project(self.read_out, self.project(self.read_in, hidden))
                final_h = bf(hidden + self.bound*correction.tanh())
                scores = self.project(self.weights['embed_tokens.weight'], final_h)[0]+self.lexical_bias
                if identity_active:
                    edit = 22 * ((self.identity_features(hidden) @ rows.T)[0]/22).tanh()
                    scores.index_add_(0, identity_ids, edit)
                token = int(scores.argmax().item())
            if not finished_thinking and (at_limit or token in (248044,248046)):
                generated.extend(closing)
                hidden = self.advance(torch.tensor(closing,device=self.device), session)
                finished_thinking = True
                continue
            if token in (248044,248046):
                stop_reason = 'stop'
                break
            if first_token is None:
                first_token = time.perf_counter()-start
            generated.append(token)
            if finished_thinking:
                response_count += 1
            else:
                reasoning_count += 1
                finished_thinking = '</think>' in self.tokenizer.decode(generated, skip_special_tokens=False)
            if response_count < response_tokens:
                hidden = self.advance(torch.tensor([token],device=self.device), session)
        text = self.tokenizer.decode(generated, skip_special_tokens=False)
        if thinking or text.lstrip().startswith('<think>'):
            text = text.partition('</think>')[2]
        if self.cuda:
            torch.cuda.synchronize()
        return dict(text=text.strip(), seconds=time.perf_counter()-start, first_token_seconds=first_token,
                    tokens=reasoning_count+response_count, response_tokens=response_count,
                    response_limit=response_tokens,
                    finish_reason=stop_reason, device=str(self.device), identity_active=identity_active)
