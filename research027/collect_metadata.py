"""Fetch only public metadata/configs pinned by revision; no weights or execution."""
import concurrent.futures
import datetime
import hashlib
import json
import urllib.request
from pathlib import Path

H = Path(__file__).resolve().parent
MODELS = ['Qwen/Qwen3.5-0.8B', 'qvac/BotPsy-0.8B',
          'openbmb/MiniCPM5-1B', 'LiquidAI/LFM2.5-1.2B-Thinking',
          'tiiuae/Falcon-H1-Tiny-R-0.6B', 'LiquidAI/LFM3-1.7B']


def get(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'LiquidSense-public-research/027'})
    with urllib.request.urlopen(request, timeout=25) as r:
        body = r.read(2 * 1024 * 1024)
        assert len(body) < 2 * 1024 * 1024, 'Unexpectedly large metadata'
        return json.loads(body), hashlib.sha256(body).hexdigest()


def collect(name):
    result = {'id': name, 'model_card': 'https://huggingface.co/' + name}
    try:
        meta, fingerprint = get('https://huggingface.co/api/models/' + name)
        revision = meta['sha']
        config, config_hash = get(f'https://huggingface.co/{name}/resolve/{revision}/config.json')
        result.update(revision=revision, metadata_sha256=fingerprint,
            created_at=meta.get('createdAt'), last_modified=meta.get('lastModified'),
            safetensors=meta.get('safetensors'), architecture_config=config,
            config_sha256=config_hash, license=meta.get('cardData', {}).get('license'),
            pinned_config_url=f'https://huggingface.co/{name}/resolve/{revision}/config.json')
    except Exception as error:
        result['fetch_error'] = type(error).__name__ + ': ' + str(error)
    return result


def main():
    out = H / 'official_metadata.json'
    assert not out.exists(), 'Preserve previous metadata snapshot'
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(collect, MODELS))
    out.write_text(json.dumps({'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'scope': 'public metadata and JSON configuration only; no model downloads/inference',
        'last_modified_is_not_release_date': True, 'models': rows}, ensure_ascii=False, indent=2) + '\n')
    for r in rows:
        print(json.dumps({'id': r['id'], 'revision': r.get('revision'),
            'created_at': r.get('created_at'), 'safetensors': r.get('safetensors'),
            'error': r.get('fetch_error')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
