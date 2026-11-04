"""Locked three-way evaluation; hidden oracles never enter model prompts."""
import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'rsi100'))
os.environ.setdefault('LS_CPU_THREADS','4')
import engine as e
import torch
from local_cpu.sandbox import evaluate


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('variant', choices=['original','parent','candidate'])
    args = parser.parse_args()
    locked = json.loads((HERE/'frozen.json').read_text())
    assert all(e.cr.file_hash(HERE/name) == digest for name,digest in locked['files'].items())
    assert e.cr.file_hash(ROOT/'mentor/checkpoints/negative_002_recovered.pt') == locked['candidate_sha256']
    tasks = json.loads((HERE/'prompts.json').read_text())
    oracles = json.loads((HERE/'oracles.json').read_text())
    controls = json.loads((HERE/'controls.json').read_text())
    anchors = json.loads((HERE/'anchors.json').read_text())
    path = HERE/('results_'+args.variant+'.json')
    report = json.loads(path.read_text()) if path.exists() else {
        'variant':args.variant,'status':'running','rows':[],'controls':[],
        'repeats':[], 'frozen_sha256':e.cr.file_hash(HERE/'frozen.json'),
        'backward_passes':0,'answers_in_generation_prompts':False}
    assert report['frozen_sha256'] == e.cr.file_hash(HERE/'frozen.json')
    model, meta = e.cr.load('original' if args.variant == 'original' else 'baseline')
    tok = e.cr.tokenizer()
    if args.variant != 'original':
        checkpoint = torch.load(ROOT/('rsi100/checkpoints/best.pt' if args.variant=='parent'
            else 'mentor/checkpoints/negative_002_recovered.pt'),weights_only=True)
        meta['architecture'] = e.apply(model, checkpoint)
    report['model'] = meta
    report['runtime'] = {'torch':torch.__version__,'threads':torch.get_num_threads(),
                         'cpu_quota':Path('/sys/fs/cgroup/cpu.max').read_text().strip()}
    seen = {r['id'] for r in report['rows']}
    for task in tasks:
        if task['id'] in seen:
            continue
        generated = e.cr.generate(model,tok,task['prompt'])
        generated.pop('trace')
        result = evaluate(generated['output'], oracles[task['id']])
        result.setdefault('case_passed',[False]*len(oracles[task['id']]['cases']))
        report['rows'].append({'id':task['id'],'group':task['group'],**generated,**result})
        e.cr.atomic_json(path,report)
        print('VALIDATION',args.variant,task['id'],result['passed'],result['total'],flush=True)
    seen = {r['id'] for r in report['controls']}
    for row in controls:
        if row['id'] in seen:
            continue
        generated = e.cr.generate(model,tok,row['question'],max_tokens=32)
        generated.pop('trace')
        correct, _ = e.cr.grade(generated['output'],row)
        report['controls'].append({'id':row['id'],'domain':row['domain'],**generated,'correct':correct})
        e.cr.atomic_json(path,report)
        print('CONTROL',args.variant,row['id'],correct,flush=True)
    originals = {r['id']:r for r in report['rows']}
    seen = {r['id'] for r in report['repeats']}
    for index in [0,6,16,20]:
        task = tasks[index]
        if task['id'] in seen:
            continue
        generated = e.cr.generate(model,tok,task['prompt'])
        generated.pop('trace')
        result = evaluate(generated['output'],oracles[task['id']])
        bits = result.get('case_passed',[False]*len(oracles[task['id']]['cases']))
        same = generated['output']==originals[task['id']]['output'] and bits==originals[task['id']]['case_passed']
        report['repeats'].append({'id':task['id'],**generated,**result,'identical':same})
        e.cr.atomic_json(path,report)
        assert same,'Greedy output unstable; stop without claiming a gain'
    if 'anchor' not in report:
        report['anchor'] = e.cr.likelihood(model,tok,anchors,anchors=True)
    report.update(status='complete',completed_unix=time.time())
    e.cr.atomic_json(path,report)
    print('VARIANT_COMPLETE',args.variant,flush=True)


if __name__=='__main__':
    main()
