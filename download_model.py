"""Download the exact public upstream revision; never execute remote model code."""
import concurrent.futures
import hashlib
import json
import pathlib
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
INFO = json.loads((ROOT / 'hf_model_info.json').read_text())
REVISION = INFO['sha']
DEST = ROOT / 'upstream'
DEST.mkdir(exist_ok=True)
FILES = ['config.json', 'tokenizer.json', 'tokenizer_config.json',
         'chat_template.jinja', 'model.safetensors.index.json', 'LICENSE',
         'preprocessor_config.json', 'video_preprocessor_config.json',
         'model.safetensors-00001-of-00001.safetensors']

def download(name):
    target = DEST / name
    if target.exists():
        return {'name': name, 'bytes': target.stat().st_size, 'reused': True}
    url = f'https://huggingface.co/Qwen/Qwen3.5-0.8B/resolve/{REVISION}/{name}'
    tmp = target.with_name(target.name + '.partial')
    digest = hashlib.sha256()
    start = time.monotonic()
    with urllib.request.urlopen(url, timeout=120) as response, tmp.open('wb') as out:
        expected = response.headers.get('Content-Length')
        size = 0
        mark = 0
        while chunk := response.read(4 * 1024 * 1024):
            out.write(chunk)
            digest.update(chunk)
            size += len(chunk)
            if size - mark >= 128 * 1024 * 1024:
                print(f'{name}: {size / 2**20:.0f} MiB', flush=True)
                mark = size
        if expected and size != int(expected):
            raise IOError(f'Incomplete {name}: {size} != {expected}')
    tmp.replace(target)
    return {'name': name, 'bytes': size, 'sha256': digest.hexdigest(),
            'seconds': round(time.monotonic() - start, 2)}

if __name__ == '__main__':
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(download, FILES):
            results.append(result)
            print(json.dumps(result), flush=True)
    (ROOT / 'download_manifest.json').write_text(json.dumps({
        'model': INFO['id'], 'revision': REVISION, 'files': results}, indent=2))
