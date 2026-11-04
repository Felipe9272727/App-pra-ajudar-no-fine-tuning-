"""Recover only unpublished hypothesis-002 work; checkpoint each completed row."""
import argparse
import copy
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'rsi100'))
os.environ.setdefault('LS_CPU_THREADS', '4')
import engine as e
import torch
from checkpoint_io import tensor_checkpoint
from local_cpu.sandbox import evaluate
from policy import accept_paired

HERE = ROOT / 'mentor/recovery_004'
PARENT_HASH = '46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'
e.cr.evaluate = evaluate


def save(name, data):
    e.cr.atomic_json(HERE / name, data)


@torch.inference_mode()
def recover(model, tok, parent):
    old = json.loads((ROOT / 'mentor/trial_002.json').read_text())
    assert e.cr.file_hash(e.CK / 'best.pt') == PARENT_HASH
    task = next(t for t in e.DATA['search'] if t['id'] == 'overlap_count')
    prompt = e.cr.prompt(tok, task['prompt'])
    states = []
    weight = model.model.language_model.layers[31].mlp.down_proj
    hook = weight.register_forward_pre_hook(
        lambda module, inputs: states.append(inputs[0][0, -1].detach().float().clone()))
    try:
        torch.manual_seed(0)
        result = model.generate(input_ids=prompt, max_new_tokens=160, use_cache=True,
                                do_sample=False, pad_token_id=tok.eos_token_id,
                                return_dict_in_generate=True, output_scores=True)
    finally:
        hook.remove()
    ids = result.sequences[0, prompt.shape[1]:].tolist()
    assert ids == old['parent_token_ids'], 'Parent tokens changed; do not claim recovery'
    assert len(states) == len(ids) == len(result.scores)
    target = old['target_index']
    h = states[target]
    preserve = torch.stack(states[:target])
    ridge = 1e-5 * float(preserve.square().sum(1).mean())
    direction = h - preserve.T @ torch.linalg.solve(
        preserve @ preserve.T + ridge * torch.eye(len(preserve)), preserve @ h)
    direction /= direction.norm()
    output = model.get_output_embeddings().weight[ids[target]].detach().float().clone()
    output /= output.norm()
    candidate = copy.deepcopy(parent)
    norm = parent['dense_weight'].float().norm()
    candidate['dense_weight'] = (parent['dense_weight'].float() -
        .012 * norm * torch.outer(output, direction)).to(parent['dense_weight'].dtype)
    candidate['mentor_trial'] = 2
    path = ROOT / 'mentor/checkpoints/negative_002_recovered.pt'
    tensor_checkpoint(candidate, path)
    tensor_checkpoint({'input_direction': direction, 'output_direction': output,
                       'target_activation': h, 'preserved_activations': preserve},
                      HERE / 'directions_002.pt')
    for key in ['history', 'router_bias']:
        assert all(torch.equal(parent[key][k], candidate[key][k]) for k in parent[key])
    delta = candidate['dense_weight'].float() - parent['dense_weight'].float()
    report = {'status': 'candidate_recovered_frozen_before_validation',
        'parent_sha256': PARENT_HASH, 'candidate_sha256': e.cr.file_hash(path),
        'checkpoint': str(path.relative_to(ROOT)), 'actual_relative_norm': float(delta.norm()/norm),
        'changed_values': int((candidate['dense_weight'] != parent['dense_weight']).sum()),
        'old_report_relative_norm': old['actual_relative_norm'],
        'old_report_changed_values': old['changed_values'],
        'parent_tokens_identical': True, 'tensor': 'model.language_model.layers.31.mlp.down_proj.weight',
        'shape': list(delta.shape), 'dtype': str(candidate['dense_weight'].dtype),
        'all_other_tensor_groups_identical': True,
        'recovery_is_not_proof_of_unsaved_candidate_bitwise_identity': True,
        'backward_passes': 0, 'architecture': e.apply(model, candidate),
        'new_validation_observed': False, 'checkpoint_promoted': False,
        'runtime': {'torch': torch.__version__, 'threads': torch.get_num_threads(),
                    'cpu_quota': Path('/sys/fs/cgroup/cpu.max').read_text().strip()},
        'created_unix': time.time()}
    save('frozen.json', report)
    print('RECOVERED', json.dumps(report), flush=True)
    return candidate


@torch.inference_mode()
def score(model, tok, variant):
    path = HERE / ('development_' + variant + '.json')
    fingerprint = e.cr.file_hash(ROOT / 'mentor/checkpoints/negative_002_recovered.pt') if variant == 'candidate' else PARENT_HASH
    data = json.loads(path.read_text()) if path.exists() else {
        'variant': variant, 'checkpoint_sha256': fingerprint, 'rows': [], 'controls': [],
        'data_sha256': e.DATA_HASH, 'status': 'running', 'backward_passes': 0}
    assert data['checkpoint_sha256'] == fingerprint and data['data_sha256'] == e.DATA_HASH
    completed = {r['id'] for r in data['rows']}
    for task in e.DATA['search'] + e.DATA['guard']:
        if task['id'] in completed:
            continue
        data['rows'] += e.coding(model, tok, [task])
        save(path.name, data)
    completed = {r['id'] for r in data['controls']}
    for row in e.DATA['search_controls']:
        if row['id'] in completed:
            continue
        data['controls'] += e.quality(model, tok, [row])
        save(path.name, data)
    data['control_bits'] = [r['correct'] for r in data['controls']]
    if 'anchor_nll' not in data:
        data['anchor_nll'] = e.cr.likelihood(model, tok, e.DATA['anchors'], anchors=True)['mean_nll']
    data['status'] = 'complete'
    save(path.name, data)
    print('FULL_SCORE', variant, sum(x['all_passed'] for x in data['rows']),
          sum(x['passed'] for x in data['rows']), data['control_bits'], data['anchor_nll'], flush=True)
    return data


@torch.inference_mode()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['recover', 'parent', 'candidate', 'gate'])
    args = parser.parse_args()
    HERE.mkdir(parents=True, exist_ok=True)
    if args.phase == 'gate':
        paired = json.loads((HERE/'development_parent.json').read_text())
        candidate = json.loads((HERE/'development_candidate.json').read_text())
        assert paired['status'] == candidate['status'] == 'complete'
        historical = json.loads((e.HERE/'best_metrics.json').read_text())
        ok, reason = accept_paired(candidate, paired, historical)
        save('development_gate.json', {'eligible_for_fresh_validation': ok, 'reason': reason,
                                     'checkpoint_promoted': False, 'backward_passes': 0})
        print('DEVELOPMENT_GATE', ok, reason, flush=True)
        return
    model, _ = e.cr.load('baseline')
    tok = e.cr.tokenizer()
    parent = e.read_checkpoint('best.pt')
    e.apply(model, parent)
    if args.phase == 'recover':
        assert not (HERE/'frozen.json').exists(), 'Candidate already recovered; do not rerun'
        recover(model, tok, parent)
    else:
        if args.phase == 'candidate':
            candidate = torch.load(ROOT/'mentor/checkpoints/negative_002_recovered.pt', weights_only=True)
            e.apply(model, candidate)
        score(model, tok, args.phase)


if __name__ == '__main__':
    main()
