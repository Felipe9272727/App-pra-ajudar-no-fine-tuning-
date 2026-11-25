"""Fit an activation classifier and sparse identity weights at the vocabulary head."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fit_identity import PARAMETERS, PREVIOUS, embeddings, load_adapter, rounded, softmax, write

# The coefficient on the constant feature is part of the architecture.
BIAS = .25
CAP = 22.


def features(states):
    vectors = np.asarray(states, dtype=np.float32)
    unit = vectors / np.maximum(1e-6, np.linalg.norm(vectors, axis=1, keepdims=True))
    return np.concatenate((unit, np.full((len(vectors),1), BIAS, dtype=np.float32)), axis=1)


def fp_bits(x):
    from fit_identity import real
    from fit import as_bits
    words = as_bits(x)
    return words, real(words)


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def fit_gate(rows):
    x = features([row['positions'][0]['hidden'] for row in rows])
    label = np.array([row['domain'] in ('identity','gate_yes') for row in rows])
    train = np.array([row['split'] == 'train' for row in rows])
    tx, ty = x[train], label[train]
    observation = np.where(ty, .5/ty.sum(), .5/(~ty).sum())
    gram = tx @ tx.T
    weight = tx.T @ np.linalg.solve(gram + np.diag(.012 / observation), 2*ty.astype(float)-1)
    bits, weight = fp_bits(weight)
    scores = x @ weight
    positives, negatives = scores[~train & label], scores[~train & ~label]
    threshold = max(.02, float(negatives.max()) + .025)
    report = {'threshold':threshold, 'train':int(train.sum()), 'dev':int((~train).sum()),
              'dev_positive':positives.tolist(), 'dev_negative':negatives.tolist(),
              'dev_positive_detected':int((positives>=threshold).sum()),
              'dev_false_positive':int((negatives>=threshold).sum())}
    return bits, threshold, report


def fit_output(rows, checkpoint, adapter):
    info, matrix_a, matrix_b = load_adapter(adapter)
    rows = [(row, point) for row in rows if row['domain']=='identity' for point in row['positions']]
    states = np.asarray([point['hidden'] for _,point in rows], dtype=np.float32)
    x = features(states)
    final = rounded(states + info['bound'] * np.tanh(rounded(rounded(states @ matrix_a.T) @ matrix_b.T)))
    labels = np.asarray([point['labels'] for _,point in rows], dtype=np.int64)
    original = np.asarray([point['scores'] for _,point in rows], dtype=np.float32)
    training = np.array([row['split']=='train' for row,_ in rows])
    targets = np.unique(labels[training,0])
    raw = rounded(final @ embeddings(checkpoint, targets.reshape(1,-1))[0].T)
    raw[:,targets>=248070] -= .75
    for i,k in enumerate(targets):
        matched = labels==k
        present = matched.any(1)
        raw[present,i] = (original * matched)[present].sum(1)
    frozen = original.copy()
    frozen[np.isin(labels,targets)] = -1e8
    expected = np.searchsorted(targets, labels[:,0])
    known = np.isin(labels[:,0],targets)
    expected[~known] = len(targets)
    plain = np.concatenate((raw,frozen),axis=1)
    norm = float(training.sum())

    def predict(weights):
        response = x @ weights.T
        return np.concatenate((raw + CAP*np.tanh(response/CAP),frozen),axis=1), response

    def metrics(logits, mask):
        loc = np.nonzero(mask)[0]
        _, logp = softmax(logits[loc])
        return {'top1':int((logits[loc].argmax(1)==expected[loc]).sum()),
                'tokens':int(len(loc)), 'cross_entropy':float(-logp[np.arange(len(loc)),expected[loc]].mean())}

    matrix = np.zeros((len(targets),1025),dtype=np.float32)
    first, second = np.zeros_like(matrix), np.zeros_like(matrix)
    best = None
    trace = []
    for step in range(1,361):
        scores, response = predict(matrix)
        grads,_ = softmax(scores)
        grads[np.arange(len(x)),expected] -= 1
        grads[~training] = 0.
        grads = grads[:,:len(targets)] * (1 - np.tanh(response/CAP)**2) / norm
        update = grads.T @ x + .00012*matrix
        first = .9*first+.1*update
        second = .999*second+.001*update**2
        matrix -= .18*(first/(1-.9**step))/(np.sqrt(second/(1-.999**step))+1e-8)
        if step in (50,90,150,230,360):
            bits, stored = fp_bits(matrix)
            scores,_ = predict(stored)
            dev = metrics(scores,~training)
            trace.append(dict(step=step,train=metrics(scores,training),dev=dev))
            key = dev['cross_entropy']
            if best is None or key < best[0]:
                best = (key,step,bits)
    _, step, bits = best
    return targets.astype(np.int32), bits, {
        'training_positions':int(training.sum()), 'validation_positions':int((~training).sum()),
        'baseline':metrics(plain,~training), 'trace':trace,'selected_step':step,
    }


def main(args):
    rows = read(args.positions)
    extra = read(args.gate)
    gate, threshold, gate_report = fit_gate(rows + extra)
    ids, output, fit_report = fit_output(rows, args.checkpoint, args.adapter)
    metadata = json.dumps(dict(format='liquid-sense-identity-head-v1', parent_adapter=PREVIOUS))
    args.output.mkdir(parents=True,exist_ok=True)
    chosen = args.output/'identity-head.npz'
    np.savez_compressed(chosen, gate=gate, threshold=np.float32(threshold), ids=ids,
                        matrix=output, metadata=np.array(metadata))
    extra_parameters = int(output.size + gate.size)
    (args.output/'head-fit.json').write_text(json.dumps({
        'sha256':hashlib.sha256(chosen.read_bytes()).hexdigest(),
        'parameter_count':PARAMETERS+extra_parameters, 'additional_parameters':extra_parameters,
        'gate':gate_report, 'readout':fit_report,
    },indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkpoint','adapter','positions','gate','output'):
        parser.add_argument(name,type=Path)
    main(parser.parse_args())
