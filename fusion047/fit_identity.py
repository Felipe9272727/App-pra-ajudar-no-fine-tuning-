"""Continue supervised training of the existing 046 readout factor."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'fusion046'))
from fit import embeddings, real, rounded, softmax, write

PREVIOUS = '941daca310736af121cdd337317b5e1bddb741b88ea085d684d3760ecc1fecfd'
PARAMETERS = 1_432_249_520


def load_adapter(path):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PREVIOUS and raw[:8] == b'LSCAL046'
    (n,) = struct.unpack('<I', raw[8:12])
    info = json.loads(raw[12:12+n])
    weights = real(np.frombuffer(raw, dtype='<u2', offset=12+n))
    assert info['rank'] == 48 and len(weights) == 2 * 48 * 1024
    return info, weights[:48*1024].reshape(48, 1024), weights[48*1024:].reshape(1024, 48)


def main(checkpoint, adapter, positions, samples, output):
    info, a, before = load_adapter(adapter)
    catalog = json.loads(samples.read_text())
    scans = [json.loads(line) for line in positions.read_text().splitlines()]
    assert [r['id'] for r in scans] == [r['id'] for r in catalog]
    rows = [(r, point) for r in scans for point in r['positions']]
    hidden = np.array([p['hidden'] for _,p in rows], dtype=np.float32)
    initial = np.array([p['scores'] for _,p in rows], dtype=np.float32)
    ids = np.array([p['labels'] for _,p in rows], dtype=np.int64)
    weights = embeddings(checkpoint, ids)
    feature = rounded(hidden @ a.T)
    training = np.array([r['split'] == 'train' for r,_ in rows])
    identity = np.array([r['domain'] == 'identity' for r,_ in rows])
    facts = np.array([r['domain'] == 'fact' for r,_ in rows])
    retain = ~(identity | facts)
    reference, reference_log = softmax(initial)
    bound = info['bound']
    old_h = rounded(hidden + bound * np.tanh(rounded(feature @ before.T)))

    def forward(b, quantized):
        raw = feature @ b.T
        if quantized:
            raw = rounded(raw)
        final_h = hidden + bound*np.tanh(raw)
        if quantized:
            final_h = rounded(final_h)
        return initial + np.einsum('nkl,nl->nk', weights, final_h - old_h), raw

    def snapshot(logits):
        _, logp = softmax(logits)
        out = {}
        for split, mask in [('train', training), ('dev', ~training)]:
            row = {}
            for name, selected in [('identity', identity), ('fact', facts)]:
                pick = mask & selected
                row[name] = dict(tokens=int(pick.sum()), top1=int((logits[pick].argmax(1)==0).sum()),
                                 cross_entropy=float(-logp[pick, 0].mean()))
            pick = mask & retain
            row['retain'] = dict(tokens=int(pick.sum()),
                                 same_top1=int((logits[pick].argmax(1)==initial[pick].argmax(1)).sum()),
                                 kl=float((reference[pick]*(reference_log[pick]-logp[pick])).sum(1).mean()))
            out[split] = row
        return out

    supervised = np.zeros(len(rows), dtype=np.float32)
    supervised[training & identity] = .87 / np.count_nonzero(training & identity)
    supervised[training & facts] = .13 / np.count_nonzero(training & facts)
    weights_retain = (training & retain).astype(np.float32)
    weights_retain /= weights_retain.sum()
    baseline = snapshot(initial)
    output.mkdir(parents=True, exist_ok=True)
    reports = {}
    for name, protection in [('preserve', 2.5), ('identity', .8)]:
        b = before.copy()
        moment, variance = np.zeros_like(b), np.zeros_like(b)
        best, curve = None, []
        for step in range(1, 181):
            logits, raw = forward(b, False)
            probs, _ = softmax(logits)
            grad = probs.copy()
            grad[:,0] -= 1
            grad = grad*supervised[:,None] + (probs-reference)*(protection*weights_retain[:,None])
            dh = np.einsum('nk,nkl->nl', grad, weights) * (bound*(1-np.tanh(raw)**2))
            diff = dh.T @ feature + .002*(b-before)
            moment = .9*moment + .1*diff
            variance = .999*variance + .001*diff**2
            rate = .011*(.45 + .55*(1+math.cos(step*math.pi/180))/2)
            b -= rate*(moment/(1-.9**step))/(np.sqrt(variance/(1-.999**step))+1e-8)
            if step in (12, 24, 48, 72, 120, 180):
                stored = rounded(b)
                result = snapshot(forward(stored, True)[0])
                dev = result['dev']
                loss = dev['identity']['cross_entropy'] + .3*dev['fact']['cross_entropy'] + 2*dev['retain']['kl']
                curve.append(dict(step=step, loss=loss, **result))
                if best is None or loss < best[0]:
                    best = (loss, step, stored)
        _, step, chosen = best
        assert np.isfinite(chosen).all()
        meta = dict(info, identity_parent=PREVIOUS, identity_step=step)
        receipt = write(output/f'{name}.lscal', meta, a, chosen)
        receipt.update(step=step, edited_coefficients=int(np.count_nonzero(chosen!=before)), curve=curve)
        reports[name] = receipt
    (output/'fit.json').write_text(json.dumps(dict(parent=PREVIOUS, parameters=PARAMETERS,
        samples=len(scans), positions=len(rows), baseline=baseline, candidates=reports),indent=2)+'\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('checkpoint', 'adapter', 'positions', 'samples', 'output'):
        p.add_argument(key, type=Path)
    main(**vars(p.parse_args()))
