"""Recover pinned public benchmark assets without changing selected test IDs."""
import hashlib
import json
from pathlib import Path
import urllib.request

HERE=Path(__file__).resolve().parent


def fetch(url,path,expected=None):
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        temp=path.with_name(path.name+'.partial')
        with urllib.request.urlopen(url,timeout=120) as source,temp.open('wb') as out:
            while data:=source.read(1024*1024):out.write(data)
        temp.replace(path)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if expected:assert digest==expected,(path,digest)
    print('PINNED_SOURCE',path.name,digest,flush=True)


def main():
    sources=json.loads((HERE/'sources.json').read_text())
    l=sources['lcb'];g=sources['gsm8k'];i=sources['ifeval']
    fetch('https://huggingface.co/datasets/livecodebench/code_generation_lite/resolve/'+l['revision']+'/'+l['file'],HERE/'lcb_v6.jsonl',l['sha256'])
    fetch('https://raw.githubusercontent.com/openai/grade-school-math/'+g['revision']+'/'+g['file'],HERE/'gsm8k_test.jsonl',g['sha256'])
    folder=HERE/'vendor/instruction_following_eval'
    for name in ['instructions.py','instructions_registry.py','instructions_util.py','evaluation_lib.py','README.md','data/input_data.jsonl']:
        fetch('https://raw.githubusercontent.com/google-research/google-research/'+i['revision']+'/instruction_following_eval/'+name,folder/name)
    (folder/'__init__.py').touch(exist_ok=True)


if __name__=='__main__':main()
