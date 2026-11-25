"""Calibrate a rank-32 residual with frozen Liquid and Gemma tensors."""
import argparse
import hashlib
import json
from pathlib import Path

import torch
from torch.nn.functional import cross_entropy

from pack import LIQUID, RANK, embeddings, read_pack, rows, write_pack


def rounded(tensor):
    return tensor.to(torch.bfloat16).float()


def main():
    parser = argparse.ArgumentParser()
    for name in ('locator', 'seed', 'features', 'output', 'report'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    torch.set_num_threads(2)
    meta, tensors = read_pack(args.seed)
    assert not meta['trained']
    samples = [json.loads(line) for line in args.features.read_text().splitlines()]
    training = torch.tensor([row['split'] == 'train' for row in samples])
    sets = {'train': training, 'validation': ~training}
    gemma = torch.tensor([row['gemma'] for row in samples])
    base = torch.tensor([row['base_scores'] for row in samples])
    labels = torch.tensor([row['labels'] for row in samples])
    assert set(row['split'] for row in samples) == set(sets)
    assert training.sum() >= RANK and torch.isfinite(gemma).all() and torch.isfinite(base).all()
    assert base.shape == labels.shape and labels.shape[1] == 16

    # Use only training activations to choose a low-dimensional coordinate system.
    _, _, right = torch.linalg.svd(gemma[training], full_matrices=False)
    basis = right[:RANK]
    rms = (gemma[training] @ basis.T).square().mean(dim=0).sqrt()
    basis = rounded(basis / rms.clamp_min(0.35)[:, None])
    encoded = rounded(gemma @ basis.T)

    vocabulary = embeddings(args.locator)
    local_ids, lookup = labels.unique(return_inverse=True)
    unrolled = rows(vocabulary, local_ids.numpy())
    first = meta['tokens'][0]['id']
    new = local_ids >= first
    unrolled[new] = tensors['lexicon'][local_ids[new] - first]
    candidates = unrolled[lookup]

    target = torch.zeros(len(samples), dtype=torch.long)
    output = torch.nn.Parameter(torch.zeros(LIQUID, RANK))
    optimizer = torch.optim.AdamW([output], lr=0.02, weight_decay=0.01)

    def predict(weights, quantized=False):
        residual = encoded @ weights.T
        if quantized:
            residual = rounded(residual)
        delta = meta['delta_limit'] * residual.tanh()
        return base + torch.bmm(candidates, delta.unsqueeze(-1)).squeeze(-1), delta

    @torch.no_grad()
    def measure(logits):
        return {name: {'cross_entropy_16': cross_entropy(logits[mask], target[mask]).item(),
                       'top1_16': int((logits[mask].argmax(dim=1) == target[mask]).sum()),
                       'tokens': int(mask.sum())}
                for name, mask in sets.items()}

    reference = measure(base)
    checkpoints = []
    selected = None
    for step in range(1, 61):
        optimizer.zero_grad()
        logits, delta = predict(output)
        objective = cross_entropy(logits[training], target[training]) + 0.10 * delta[training].square().mean()
        objective.backward()
        optimizer.step()
        if step in (15, 30, 45, 60):
            with torch.no_grad():
                stored = rounded(output)
                logits, delta = predict(stored, quantized=True)
                record = {'step': step, **measure(logits), 'max_calibration_delta': delta.abs().max().item()}
                checkpoints.append(record)
                error = record['validation']['cross_entropy_16']
                if selected is None or error < selected[0]:
                    selected = error, stored.clone(), record

    _, weights, record = selected
    assert torch.isfinite(weights).all() and torch.count_nonzero(weights)
    tensors['feature'] = basis
    tensors['output'] = weights
    meta.update(trained=True, fit={'method': 'frozen-feature rank-32 AdamW',
                'best_step': record['step'], 'train_tokens': int(training.sum()),
                'validation_tokens': int((~training).sum())})
    write_pack(args.output, meta, tensors)
    with args.output.open('rb') as stream:
        checkpoint_sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    report = {'checkpoint': args.output.name, 'sha256': checkpoint_sha,
              'bytes': args.output.stat().st_size, 'trained_coefficients': LIQUID * RANK,
              'heldout_lexicon_only': reference, 'checkpoints': checkpoints, 'selected': record,
              'scope': 'Teacher-forced, 16 candidate ids per position. Free generation is evaluated separately.'}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'sha256': checkpoint_sha, 'baseline': reference, 'fitted': record}))


if __name__ == '__main__':
    main()
