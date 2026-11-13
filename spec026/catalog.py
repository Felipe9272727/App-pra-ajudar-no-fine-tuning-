"""Catalog frozen dependencies and complete study artifacts for remote verification."""
import hashlib
import json
from pathlib import Path
from io_parts import file_hash, save_json

H = Path(__file__).resolve().parent
ROOT = H.parent


def identity(path):
    size = path.stat().st_size
    sha256 = hashlib.sha256()
    blob = hashlib.sha1(f'blob {size}\0'.encode())
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            sha256.update(chunk)
            blob.update(chunk)
    return {'path': str(path.relative_to(ROOT)), 'bytes': size,
            'sha256': sha256.hexdigest(), 'git_blob_sha1': blob.hexdigest()}


def main():
    status = json.loads((H / 'status.json').read_text())
    assert status['model_process_active'] is False
    assert json.loads((H / 'summary.json').read_text())['status'].startswith('complete')
    frozen = json.loads((H / 'frozen.json').read_text())
    assert all(file_hash(ROOT / p) == s for p, s in frozen.items())
    auxiliary = json.loads((H / 'auxiliary_sources.json').read_text())
    assert all(file_hash(ROOT / p) == s for p, s in auxiliary.items())
    assert file_hash(ROOT / 'rsi100/checkpoints/best.pt') == '46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'
    excluded = {'artifact_manifest.json', 'remote_verification.json'}
    paths = {p for p in H.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name not in excluded and not p.name.endswith('.tmp')}
    # pathlib.rglob does not descend through the top-level checkpoint symlink.
    paths.update(p for p in (H / 'checkpoints').rglob('*') if p.is_file())
    paths.update(ROOT / p for p in frozen)
    rows = [identity(p) for p in sorted(paths)]
    save_json(H / 'artifact_manifest.json', {'status': 'complete', 'files': rows,
              'file_count': len(rows), 'total_bytes': sum(r['bytes'] for r in rows),
              'frozen_sources_and_data_unchanged': True, 'target_parent_hash_unchanged': True,
              'model_workers_closed': True,
              'excluded_self_and_remote_receipt': sorted(excluded)})
    print('CATALOG026', len(rows), sum(r['bytes'] for r in rows), flush=True)


if __name__ == '__main__':
    main()
