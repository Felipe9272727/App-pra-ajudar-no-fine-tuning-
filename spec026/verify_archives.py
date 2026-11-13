"""Cold-load every saved phase and verify exact parameter and archive identities."""
import gc
import json
from pathlib import Path
import torch
from draft_model import tensor_hash
from io_parts import load_parts, save_json

H = Path(__file__).resolve().parent


def main():
    torch.set_num_threads(4)
    rows = []
    for size in ['small', 'large']:
        initial = json.loads((H / 'reports' / f'initial_{size}.json').read_text())
        trained = json.loads((H / 'reports' / f'training_{size}.json').read_text())
        for phase, key in [('initial', 'parameter_hashes'), ('final', 'final_FP32_hashes'), ('inference', 'inference_hashes')]:
            expected = (initial if phase == 'initial' else trained)[key]
            payload, manifest = load_parts(H / 'checkpoints' / size / phase)
            state = payload['model']
            assert all(tensor_hash(state[n]) == h for n, h in expected.items())
            assert all(bool(torch.isfinite(t).all()) for t in state.values() if t.is_floating_point())
            if phase == 'final':
                assert payload['step'] == trained['optimizer_steps']
                assert len(payload['optimizer']['state']) == len(expected)
                assert payload['rng'].dtype == torch.uint8
            rows.append({'size': size, 'phase': phase, 'parameter_tensors_verified': len(expected),
                         'compressed_sha256': manifest['compressed_sha256'],
                         'compressed_bytes': manifest['compressed_bytes'], 'all_finite': True,
                         'optimizer_and_rng_restored': phase == 'final'})
            del state, payload
            gc.collect()
            print('COLD_ARCHIVE_VERIFIED', size, phase, flush=True)
    save_json(H / 'reports' / 'cold_archive_verification.json', {'complete': True, 'rows': rows})


if __name__ == '__main__':
    main()
