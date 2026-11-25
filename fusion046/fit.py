"""Fit the readout on frozen Gemma 045 activations and calibrate both loop visits."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np

from recover import SHA

RANK, CORE = 48, 1024
BOUND = 0.32
NEW_TOKEN = 248070
WEIGHTS = dict(code=0.45, reason=0.33, language=0.22)


def as_bits(x):
    u = np.ascontiguousarray(x, dtype=np.float32).view(np.uint32)
    return ((u + 0x7fff + ((u >> 16) & 1)) >> 16).astype('<u2')


def real(bits):
    return (bits.astype(np.uint32) << 16).view(np.float32)


def rounded(x):
    return real(as_bits(x))


def embeddings(checkpoint, labels):
    with checkpoint.open('rb') as file:
        assert file.read(8) == b'LSMIX045'
        size, = struct.unpack('<I', file.read(4))
        mix = json.loads(file.read(size))
        base = mix['base']['offset']
        file.seek(base)
        assert file.read(8) == b'LSENSE01'
        size, = struct.unpack('<Q', file.read(8))
        parent = json.loads(file.read(size))
    entry = parent['tensors']['embed_tokens.weight']
    assert entry['shape'] == [248320, CORE] and entry['kind'] == 'bf16'
    base_rows = np.memmap(checkpoint, mode='r', dtype='<u2', shape=(248320, CORE),
                         offset=base + entry['offset'])
    new_rows = np.memmap(checkpoint, mode='r', dtype='<u2', shape=(129, CORE),
                        offset=mix['alignment']['offset'] + 4 * CORE * 1152)
    ids, indices = np.unique(labels, return_inverse=True)
    selected = base_rows[ids]
    new = ids >= NEW_TOKEN
    assert np.all(ids[new] < NEW_TOKEN + 129)
    selected[new] = new_rows[ids[new] - NEW_TOKEN]
    return np.ascontiguousarray(real(selected)[indices.reshape(labels.shape)])


def softmax(scores):
    high = scores.max(axis=1, keepdims=True)
    logits = scores - high
    exp = np.exp(logits)
    counts = exp.sum(axis=1, keepdims=True)
    return exp / counts, logits - np.log(counts)


def write(path, meta, down, up):
    payload = json.dumps(meta, sort_keys=True, separators=(',', ':')).encode()
    data = b'LSCAL046' + struct.pack('<I', len(payload)) + payload
    data += as_bits(down).tobytes() + as_bits(up).tobytes()
    path.write_bytes(data)
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
            'bound': meta['bound'], 'gains': meta['gains']}


def fit(checkpoint, positions, corpus, out):
    catalog = json.loads(corpus.read_text())
    scans = [json.loads(line) for line in positions.read_text().splitlines()]
    assert [row['id'] for row in scans] == [row['id'] for row in catalog]
    for scan, row in zip(scans, catalog):
        assert (scan['split'], scan['domain'], scan['retention']) == (
            row['split'], row['domain'], row['completion'] is None)

    samples = [(row, point) for row in scans for point in row['positions']]
    hidden = np.array([p['hidden'] for _, p in samples], dtype=np.float32)
    telemetry = np.array([p['gemma_response'] for _, p in samples], dtype=np.float32)
    scores = np.array([p['scores'] for _, p in samples], dtype=np.float32)
    labels = np.array([p['labels'] for _, p in samples], dtype=np.int64)
    trains = np.array([r['split'] == 'train' for r, _ in samples])
    retain = np.array([r['retention'] for r, _ in samples])
    domains = np.array([r['domain'] for r, _ in samples])
    expected_count = (len(samples), 24)
    assert hidden.shape == (len(samples), CORE) and telemetry.shape == (len(samples), 38)
    assert scores.shape == labels.shape == expected_count and np.isfinite(scores).all()
    assert np.isfinite(hidden).all() and np.all((telemetry > 0) & (telemetry <= 1))
    lookup = embeddings(checkpoint, labels)
    reference, log_reference = softmax(scores)
    row_weights = np.zeros(len(samples), dtype=np.float32)
    for domain, portion in WEIGHTS.items():
        one = trains & (domains == domain)
        row_weights[one] = portion / one.sum()
    anchor_weights = np.zeros(len(samples), dtype=np.float32)
    anchor_weights[trains & retain] = 0.85 / (trains & retain).sum()

    _, _, vh = np.linalg.svd(hidden[trains], full_matrices=False)
    basis = vh[:RANK].copy()
    rms = np.sqrt(np.mean(np.square(hidden[trains] @ basis.T), axis=0))
    basis = rounded(basis / np.maximum(rms[:, None], 0.25))
    features = rounded(hidden @ basis.T)

    def predict(patch, quantized=False):
        residual = features @ patch.T
        correction = BOUND * np.tanh(rounded(residual) if quantized else residual)
        changed = rounded(hidden + correction) - hidden if quantized else correction
        logits = scores + np.einsum('nkl,nl->nk', lookup, changed)
        return logits, residual

    def measure(logits, mask):
        _, log_prob = softmax(logits)
        supervised = mask & ~retain
        anchors = mask & retain
        return {'tokens': int(supervised.sum()), 'positions_retain': int(anchors.sum()),
                'top1': int((logits[supervised].argmax(axis=1) == 0).sum()),
                'cross_entropy': float(-log_prob[supervised, 0].mean()),
                'retention_kl': float((reference[anchors] * (log_reference[anchors] - log_prob[anchors])).sum(axis=1).mean()),
                'by_domain': {domain: {'tokens': int((mask & (domains == domain)).sum()),
                               'cross_entropy': float(-log_prob[mask & (domains == domain),0].mean())}
                              for domain in WEIGHTS}}

    patch = np.zeros((CORE, RANK), dtype=np.float32)
    moving = np.zeros_like(patch)
    squares = np.zeros_like(patch)
    best, selected, curve = float('inf'), None, []
    for step in range(1, 161):
        logits, residual = predict(patch)
        probability, _ = softmax(logits)
        grad = probability.copy()
        grad[:, 0] -= 1
        grad = grad * row_weights[:, None] + (probability - reference) * anchor_weights[:, None]
        dh = np.einsum('nk,nkd->nd', grad, lookup)
        dh *= BOUND * (1 - np.square(np.tanh(residual)))
        grad_patch = dh.T @ features + 0.001 * patch
        moving = 0.9 * moving + 0.1 * grad_patch
        squares = 0.999 * squares + 0.001 * np.square(grad_patch)
        learning = 0.012 * (0.4 + 0.6 * (1 + math.cos(step * math.pi / 160)) / 2)
        patch -= learning * (moving / (1 - 0.9**step)) / (np.sqrt(squares / (1 - 0.999**step)) + 1e-8)
        if step in (10, 20, 40, 60, 80, 120, 160):
            stored = rounded(patch)
            proposed, _ = predict(stored, quantized=True)
            train = measure(proposed, trains)
            dev = measure(proposed, ~trains)
            selection_score = sum(v * dev['by_domain'][d]['cross_entropy'] for d, v in WEIGHTS.items()) + dev['retention_kl']
            curve.append({'step': step, 'selection_loss': selection_score, 'train': train, 'dev': dev})
            if selection_score < best:
                best, selected = selection_score, (step, stored)

    number, up = selected
    assert np.isfinite(up).all() and up.any()
    strengths = np.sqrt(np.square(telemetry[trains]).mean(axis=0))
    relative = 0.75 + 0.25 * np.median(strengths) / strengths
    relative *= np.array([0.95] * 19 + [1.05] * 19, dtype=np.float32)
    relative = np.clip(relative, 0.8, 1.2)
    # Match the sum of measured squared perturbations, redistributing strength across visits.
    gains = 0.0275 * relative * np.linalg.norm(strengths) / np.linalg.norm(strengths * relative)
    assert np.all((gains >= 0.012) & (gains <= 0.045))
    meta = {'format': 'liquid-sense-calibration-046', 'parent': SHA, 'rank': RANK,
            'bound': BOUND, 'step': number}
    candidates = {}
    out.mkdir(parents=True, exist_ok=True)
    for name, profile in [('readout', [0.0275] * 38), ('balanced', gains.astype(float).tolist())]:
        candidates[name] = write(out / f'{name}.lscal', dict(meta, gains=profile), basis, up)
    report = {'parent': SHA, 'candidates': candidates, 'chosen_fit_step': number,
              'calibration_examples': len(scans), 'calibration_positions': len(samples),
              'hard_candidates_per_position': 24, 'coefficients_optimized': int(up.size),
              'basis_coefficients': int(basis.size),
              'frozen_weights': {'liquid': 919659696, 'gemma': 510000128},
              'source_data_sha256': hashlib.sha256(corpus.read_bytes()).hexdigest(),
              'baseline': {'train': measure(scores, trains), 'dev': measure(scores, ~trains)},
              'response_rms_by_visit': strengths.tolist(), 'curve': curve}
    (out/'fit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'count': len(scans), 'positions': len(samples), 'steps': 160,
                      'selected': number, 'baseline': report['baseline']['dev'],
                      'selected_measurement': next(row['dev'] for row in curve if row['step'] == number)}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('checkpoint', 'positions', 'corpus', 'out'):
        p.add_argument(name, type=Path)
    a = p.parse_args()
    fit(a.checkpoint, a.positions, a.corpus, a.out)
