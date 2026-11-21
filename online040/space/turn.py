"""Preset-aware generation with a continuation for each ZeroGPU allocation."""
import hashlib
import json
import time

import torch
from torch.nn import functional as F

CONTEXT = 16_384
PRESETS = {'normal': (0, 2048), 'profundo': (1024, 2048), 'extenso': (2048, 4096)}
STOP = {248044, 248046}
MAX_SEGMENT = 512
DECODE_SECONDS = 22


def segment_duration(payload, request=None):
    if not isinstance(payload, dict):
        return 12
    limit = payload.get('segment_tokens', MAX_SEGMENT)
    if type(limit) is not int:
        return 12
    history = payload.get('messages')
    characters = sum(len(m.get('content', '')) for m in history
                     if isinstance(m, dict) and isinstance(m.get('content'), str)) if isinstance(history, list) else 0
    cursor = payload.get('cursor')
    previous = cursor.get('ids', []) if isinstance(cursor, dict) else []
    prior_tokens = len(previous) if isinstance(previous, list) else 0
    return min(45, 12 + max(0, min(limit, MAX_SEGMENT)) // 12 + (characters // 4 + prior_tokens) // 400)


def encode_prompt(engine, messages, profile):
    if not isinstance(messages, list) or not messages or len(messages) > 256:
        raise ValueError('Envie entre 1 e 256 mensagens de texto.')
    if any(not isinstance(m, dict) or m.get('role') not in ('user', 'assistant') or
           not isinstance(m.get('content'), str) for m in messages):
        raise ValueError('O histórico GPU aceita mensagens de usuário e assistente.')
    if messages[-1]['role'] != 'user' or not messages[-1]['content'].strip():
        raise ValueError('Escreva uma mensagem para enviar.')
    if len(messages[-1]['content']) > 64_000 or sum(len(m['content']) for m in messages) > 256_000:
        raise ValueError('A mensagem ou o histórico excede o tamanho permitido.')
    reasoning, answer = PRESETS[profile]
    # Reserve space for generation, including tokens that close thinking.
    while True:
        prompt = engine.tok.apply_chat_template(
            [{'role': 'system', 'content': engine.identity}, *messages],
            tokenize=True, add_generation_prompt=True, enable_thinking=reasoning > 0, return_dict=False,
        )
        if len(prompt) + reasoning + answer + 16 <= CONTEXT:
            return prompt
        start = next((i for i, m in enumerate(messages[1:], 1) if m['role'] == 'user'), None)
        if start is None:
            raise ValueError(f'A mensagem não cabe no contexto de {CONTEXT} tokens com este modo.')
        messages = messages[start:]


def state_from_cursor(cursor, fingerprint, think_limit, answer_limit, vocab):
    if cursor is None:
        return [], 0, 0, think_limit == 0, False
    try:
        ids, thought, answer, closed, forced = (cursor[key] for key in ('ids', 'thought', 'answer', 'closed', 'forced'))
        if (cursor['key'] != fingerprint or not isinstance(ids, list) or not ids or
                any(type(t) is not int or not 0 <= t < vocab for t in ids) or
                type(thought) is not int or type(answer) is not int or
                not 0 <= thought <= think_limit or not 0 <= answer <= answer_limit or
                type(closed) is not bool or type(forced) is not bool or
                not thought + answer <= len(ids) <= thought + answer + 16 or
                (answer and not closed) or (think_limit == 0 and (not closed or forced))):
            raise ValueError()
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('A continuação não corresponde a esta mensagem e modo.') from error
    return ids.copy(), thought, answer, closed, forced


@torch.inference_mode()
def generate_segment(engine, payload):
    if not isinstance(payload, dict) or payload.get('profile') not in PRESETS:
        raise ValueError('Modo de raciocínio inválido.')
    profile = payload['profile']
    think_limit, answer_limit = PRESETS[profile]
    prompt = encode_prompt(engine, payload.get('messages'), profile)
    fingerprint = hashlib.sha256(json.dumps([profile, prompt]).encode()).hexdigest()
    vocab = engine.text.embed_tokens.weight.shape[0]
    ids, thought, answer, closed, forced = state_from_cursor(
        payload.get('cursor'), fingerprint, think_limit, answer_limit, vocab,
    )
    raw_before = len(ids)
    began = time.monotonic()
    prefill = torch.tensor([prompt + ids], device=engine.device)
    output = engine.text(input_ids=prefill, use_cache=True)
    cache = output.past_key_values
    prefill_seconds = time.monotonic() - began
    deadline = min(began + segment_duration(payload) - 4, time.monotonic() + DECODE_SECONDS)
    decode_start = time.monotonic()
    first_token_seconds = None
    finish = 'continue'
    chunk_limit = payload.get('segment_tokens', MAX_SEGMENT)
    if type(chunk_limit) is not int or not 1 <= chunk_limit <= MAX_SEGMENT:
        raise ValueError('Tamanho inválido para a etapa de geração.')
    for _ in range(chunk_limit):
        if closed and answer >= answer_limit:
            finish = 'length'
            break
        if len(ids) > raw_before and time.monotonic() >= deadline:
            break
        at_think_limit = not closed and thought >= think_limit
        if at_think_limit:
            token = None
        else:
            logits = F.linear(output.last_hidden_state[:, -1], engine.text.embed_tokens.weight).float()
            token = int(logits.argmax(-1).item())
        if first_token_seconds is None:
            first_token_seconds = time.monotonic() - began
        if not closed and (at_think_limit or token in STOP):
            new_ids = engine.tok.encode('</think>\n\n', add_special_tokens=False)
            closed = forced = True
        elif token in STOP:
            finish = 'stop'
            break
        else:
            new_ids = [token]
            if closed:
                answer += 1
            else:
                thought += 1
        ids.extend(new_ids)
        if not closed:
            closed = '</think>' in engine.tok.decode(ids, skip_special_tokens=False)
        if closed and answer >= answer_limit:
            finish = 'length'
            break
        output = engine.text(input_ids=torch.tensor([new_ids], device=engine.device),
                             past_key_values=cache, use_cache=True)
        cache = output.past_key_values
    raw = engine.tok.decode(ids, skip_special_tokens=False)
    thought_text, separator, text = raw.partition('</think>') if think_limit else ('', '', raw)
    if think_limit and not separator:
        text = ''
    cursor = {'key': fingerprint, 'ids': ids, 'thought': thought, 'answer': answer,
              'closed': closed, 'forced': forced} if finish == 'continue' else None
    return {
        'text': text.strip(), 'thought': thought_text.strip(), 'raw_text': raw,
        'tokens': thought + answer, 'reasoning_tokens': thought, 'response_tokens': answer,
        'forced_reasoning_close': forced, 'finish_reason': finish, 'cursor': cursor,
        'prefill_seconds': prefill_seconds, 'decode_seconds': time.monotonic() - decode_start,
        'first_token_seconds': first_token_seconds,
        'device': str(engine.text.embed_tokens.weight.device),
        'limits': {'context': CONTEXT, 'thinking': think_limit, 'answer': answer_limit},
    }
