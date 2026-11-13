"""Additional original-Qwen reference, registered before any quality outputs."""
import json
import os
import time
from pathlib import Path
import torch
from target_model import tr
from io_parts import save_json
from local_cpu.sandbox import evaluate as judge
from spec_engine import Engine, serial, install_cached_recurrent_rule

H = Path(__file__).resolve().parent


@torch.inference_mode()
def main():
    install_cached_recurrent_rule()
    torch.set_num_threads(4)
    p = H / 'reports/quality_original.json'
    r = json.loads(p.read_text()) if p.exists() else {
        'variant': 'original', 'code': [], 'general': [],
        'scope': 'same new custom quality suite; additional original reference',
        'answers_or_cases_in_prompts': False}
    if r.get('status') == 'complete':
        print('ORIGINAL_ALREADY_COMPLETE')
        return
    start = time.perf_counter()
    model, meta = tr.e.cr.load('original')
    model.eval()
    model.requires_grad_(False)
    tok = tr.e.cr.tokenizer()
    r['model_load_seconds'] = time.perf_counter() - start
    r['metadata'] = meta
    engine = Engine(model, 'original')
    for split, budget in [('code', 96), ('general', 32)]:
        for row in json.loads((H / 'data' / f'quality_{split}.json').read_text()):
            if row['id'] in {x['id'] for x in r[split]}:
                continue
            question = row['prompt'] if split == 'code' else row['question']
            prefix = tok.apply_chat_template([{'role': 'user', 'content': question}],
                tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
            out = serial(engine, prefix, budget)
            out.update(id=row['id'], text=tok.decode(out['ids'], skip_special_tokens=True))
            if split == 'code':
                out.update(judge(out['text'], row))
            else:
                out['correct'] = tr.e.cr.grade(out['text'], row)[0]
            r[split].append(out)
            save_json(p, r)
            print('QUALITY026_ORIGINAL', row['id'], out.get('all_passed', out.get('correct')), flush=True)
    r.update(status='complete', code_tasks=sum(x['all_passed'] for x in r['code']),
             code_cases=sum(x['passed'] for x in r['code']),
             code_cases_total=sum(x['total'] for x in r['code']),
             general_correct=sum(x['correct'] for x in r['general']))
    save_json(p, r)


if __name__ == '__main__':
    status = json.loads((H / 'status.json').read_text())
    status.update(status='running_original_quality', model_process_active=True)
    save_json(H / 'status.json', status)
    save_json(H / 'runtime.json', {'phase': 'original_quality', 'pid': os.getpid(), 'single_worker': True})
    succeeded = False
    try:
        main()
        succeeded = True
    finally:
        status = json.loads((H / 'status.json').read_text())
        status.update(status='completed_original_quality' if succeeded else 'failed_original_quality', model_process_active=False)
        save_json(H / 'status.json', status)
        save_json(H / 'runtime.json', {'phase': 'original_quality', 'pid': None, 'model_process_active': False})
