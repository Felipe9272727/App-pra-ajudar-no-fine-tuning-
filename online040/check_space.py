"""Probe the live Space using the same HTTP/SSE contract as the Android app."""
import json
from pathlib import Path
import time
import urllib.request

from huggingface_hub import HfApi, get_token

NAME = 'Felipe0282829273/liquid-sense-gpu'
API = 'https://felipe0282829273-liquid-sense-gpu.hf.space/gradio_api/call/generate_turn'


def invoke(payload, authenticated=True):
    headers = {'Authorization': 'Bearer ' + get_token()} if authenticated else {}
    headers['Content-Type'] = 'application/json'
    data = json.dumps({'data': [payload]}).encode()
    with urllib.request.urlopen(urllib.request.Request(API, data, headers=headers), timeout=30) as response:
        event = json.load(response)['event_id']
    with urllib.request.urlopen(urllib.request.Request(API + '/' + event, headers=headers), timeout=120) as response:
        for line in response:
            if line.startswith(b'event:'):
                mode = line[6:].strip()
            elif line.startswith(b'data:') and mode in (b'complete', b'error'):
                body = json.loads(line[5:])
                if mode == b'error':
                    raise RuntimeError(str(body))
                result = body[0]
                assert result['device'].startswith('cuda'), result['device']
                return result
    raise RuntimeError('The event stream ended before a result.')


def main():
    api = HfApi()
    for _ in range(60):
        runtime = api.get_space_runtime(NAME)
        if runtime.stage == 'RUNNING':
            assert runtime.hardware == 'zero-a10g'
            break
        if runtime.stage in ('RUNTIME_ERROR', 'BUILD_ERROR', 'CONFIG_ERROR'):
            raise RuntimeError(runtime.stage)
        time.sleep(5)
    else:
        raise RuntimeError('O Space não concluiu a inicialização no prazo do teste.')
    small = {'messages': [{'role': 'user', 'content': 'Meu nome é Marina.'},
                          {'role': 'assistant', 'content': 'Olá, Marina.'},
                          {'role': 'user', 'content': 'Qual é o meu nome? Responda só o nome.'}],
             'profile': 'normal', 'segment_tokens': 1}
    first = invoke(small)
    assert first['tokens'] == 1 and first['cursor']
    continued = invoke({**small, 'cursor': first['cursor'], 'segment_tokens': 16})
    assert 'Marina' in continued['text'] and continued['limits'] == {'context': 16384, 'thinking': 0, 'answer': 2048}
    print('LIVE HISTORY AND CONTINUATION', continued['text'], flush=True)
    long = {'profile': 'extenso', 'messages': [{'role': 'user', 'content':
            'Escreva em português um guia prático detalhado de pelo menos 1500 palavras sobre como implementar passo a passo um aplicativo offline de organização de uma biblioteca. Inclua arquitetura, exemplos de dados, migração, dez fases de implementação e testes. Não termine antes de cobrir todos os passos.'}]}
    rows = []
    final = None
    for _ in range(6):
        final = invoke(long)
        rows.append({k: v for k, v in final.items() if k not in ('thought', 'raw_text', 'cursor', 'text')})
        print('LONG', final['tokens'], final['finish_reason'], flush=True)
        assert final['limits'] == {'context': 16384, 'thinking': 2048, 'answer': 4096}
        if final['tokens'] > 564 or final['finish_reason'] != 'continue':
            break
        long['cursor'] = final['cursor']
    data = {'space': NAME, 'revision': api.space_info(NAME).sha, 'transport': 'POST + SSE GET',
            'history_and_continuation': continued['text'], 'long_test': rows,
            'exceeded_564': final['tokens'] > 564}
    Path('online040/reports/live_gpu.json').write_text(json.dumps(data, indent=2) + '\n')


if __name__ == '__main__':
    main()
