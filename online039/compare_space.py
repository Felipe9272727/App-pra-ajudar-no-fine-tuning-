"""Compare Space inference to the saved CPU traces and record elapsed request time."""
import argparse
import json
import sys
import time
from pathlib import Path
from gradio_client import Client
from huggingface_hub import get_token

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_cpu.sandbox import evaluate

CASES = {
    'arithmetic': {'budget': 8},
    'code_square': {'budget': 64, 'cases': [
        {'args': [[1, 2, 3, 4]], 'expected': 20},
        {'args': [[]], 'expected': 0},
        {'args': [[-2, 3, 0]], 'expected': 4},
    ]},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('space', help='Hugging Face Space namespace/name')
    parser.add_argument('output', type=Path)
    parser.add_argument('--cpu-reference', type=Path, default=Path(__file__).parent / 'reports/cpu_parity_reference.json')
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    baseline = json.loads(args.cpu_reference.read_text())
    client = Client(args.space, token=get_token(), max_workers=1, verbose=False, analytics_enabled=False)
    rows = []
    for cpu in baseline['rows']:
        test = CASES[cpu['id']]
        started = time.perf_counter()
        answer, gpu = client.predict(cpu['prompt'], test['budget'], False, api_name='/generate')
        elapsed = time.perf_counter() - started
        if not gpu['device'].startswith('cuda') or gpu['weights_SHA256'] != baseline['pack_sha256']:
            raise ValueError('O Space não retornou o pacote esperado em CUDA')
        if 'cases' in test:
            quality = evaluate(answer, test)
        else:
            quality = {'correct': answer.strip() == '4'}
        rows.append({'id': cpu['id'], 'token_match_to_CPU': gpu['tokens'] == cpu['tokens'],
                     'quality': quality, 'gpu': gpu, 'wall_request_seconds': elapsed,
                     'cpu_reference_seconds': cpu['seconds']})
    with args.output.open('x') as output:
        json.dump({'space': args.space, 'rows': rows, 'general_benchmark': False}, output, indent=2)


if __name__ == '__main__':
    main()
