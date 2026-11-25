"""Recover verified app assets and fetch the frozen evaluation inputs."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import urlretrieve
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'speed041'))
from locate import locate

RELEASE = 'https://github.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-/releases/download/liquid-sense-0.6.3-verified035/LiquidSense-0.6.3-verificado.zip'
ROWS = 'https://datasets-server.huggingface.co/rows?'
AA = 'https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR/resolve/bdae010bbce259820c0e34c1d7cce210d966fb75/'


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def recover(folder):
    folder.mkdir(parents=True, exist_ok=True)
    name = 'LiquidSense-0.6.3-install-preview.apk'
    apk = folder/name
    if not apk.exists():
        archive = folder/'source.zip'
        urlretrieve(RELEASE, archive)
        assert digest(archive)=='52966dccfc9ec1dd6f4eaeabadaa3615c31e286034d84c04a74690042724f307'
        with zipfile.ZipFile(archive) as source:
            source.extract(name, folder)
        archive.unlink()
    (folder/'locator.json').write_text(json.dumps(locate(apk)))
    with zipfile.ZipFile(apk) as source:
        (folder/'tokenizer.json').write_bytes(source.read('assets/tokenizer.json'))


def inputs(folder):
    manifest = json.loads((ROOT/'loop042/data/evaluation_manifest.json').read_text())
    if_ref = manifest['ifbench_revision']
    sources = {
        'aime.source': ROWS+'dataset=math-ai%2Faime25&config=default&split=test&offset=0&length=30',
        'gpqa.source': 'https://huggingface.co/datasets/natong19/gpqa/resolve/main/gpqa_diamond.csv',
        'if.source': f'https://raw.githubusercontent.com/allenai/IFBench/{if_ref}/data/IFBench_test.jsonl',
        'aa.source': AA+'AA-LCR_Dataset.csv',
        'aa-text.zip': AA+'extracted_text/AA-LCR_extracted-text.zip',
    }
    for offset in [102, 1314, 2402, 4488, 6240, 9250]:
        sources[f'mmlu-{offset}.source'] = ROWS+f'dataset=TIGER-Lab%2FMMLU-Pro&config=default&split=test&length=1&offset={offset}'
    (folder/'if-ref.txt').write_text(if_ref+'\n')

    def fetch(item):
        filename, url = item
        file = folder/filename
        if not file.exists():
            urlretrieve(url, file)
        assert digest(file)==manifest['source_sha256'][filename], filename

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(fetch, sources.items()))


if __name__=='__main__':
    p = argparse.ArgumentParser()
    p.add_argument('folder', type=Path)
    args = p.parse_args()
    recover(args.folder)
    inputs(args.folder)
