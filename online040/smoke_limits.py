"""Check exact budget boundaries and cursor integrity without using GPU quota."""
from pathlib import Path
import hashlib
import json
import sys
from types import SimpleNamespace
import torch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'space'))
from turn import CONTEXT, PRESETS, encode_prompt, generate_segment


class Tokenizer:
    def apply_chat_template(self, messages, **kwargs):
        return [1] * sum(len(item['content']) for item in messages)

    def encode(self, text, **kwargs):
        assert text == '</think>\n\n'
        return [2]

    def decode(self, tokens, **kwargs):
        return ''.join('</think>\n\n' if token == 2 else 'a' for token in tokens)


class Text:
    embed_tokens = SimpleNamespace(weight=torch.tensor([[0.0], [1.0], [0.0]]))

    def __call__(self, **kwargs):
        return SimpleNamespace(last_hidden_state=torch.ones(1, 1, 1), past_key_values=())


def main():
    engine = SimpleNamespace(identity='sys', tok=Tokenizer(), text=Text(), device='cpu')
    messages = [{'role': 'user', 'content': 'texto'}]
    profile = 'extenso'
    prompt = encode_prompt(engine, messages, profile)
    fingerprint = hashlib.sha256(json.dumps([profile, prompt]).encode()).hexdigest()
    boundary = {'ids': [1] * 2048, 'key': fingerprint, 'thought': 2048, 'answer': 0, 'closed': False, 'forced': False}
    previous = {'messages': messages, 'profile': profile, 'cursor': boundary, 'segment_tokens': 2}
    close = generate_segment(engine, previous)
    assert close['forced_reasoning_close'] and close['reasoning_tokens'] == 2048 and close['response_tokens'] == 1
    assert close['cursor']['ids'][2048] == 2 and close['text'] == 'a'
    final_cursor = {**close['cursor'], 'ids': [1] * 2048 + [2] + [1] * 4095, 'answer': 4095}
    final = generate_segment(engine, {**previous, 'cursor': final_cursor})
    assert final['tokens'] == 6144 and final['finish_reason'] == 'length' and final['cursor'] is None
    assert final['limits'] == {'context': 16384, 'thinking': 2048, 'answer': 4096}
    alt = [{ 'role':'user', 'content':'different context' }]
    try:
        generate_segment(engine, {**previous, 'messages': alt})
    except ValueError as error:
        assert 'continuação' in str(error)
    else:
        raise AssertionError('Continuation unexpectedly reused across prompts')
    overflow = [{'role':'user','content':'a' * CONTEXT}]
    try:
        encode_prompt(engine, overflow, profile)
    except ValueError as error:
        assert 'contexto' in str(error)
    else:
        raise AssertionError('Overflow not rejected')
    summary = {'passed': True, 'context': CONTEXT, 'presets': PRESETS,
               'extenso_reached_cap_in_fixture': final['tokens'], 'live_model': False,
               'test': 'forced reasoning closure, exact answer cap, different context and message overflow'}
    (ROOT / 'reports/smoke_limits.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
