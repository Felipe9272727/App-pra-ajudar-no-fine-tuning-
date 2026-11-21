"""Publish the prototype as a new ZeroGPU Space under the authenticated user."""
import argparse
from pathlib import Path
from huggingface_hub import HfApi, SpaceHardware


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', default='liquid-sense-gpu')
    args = parser.parse_args()
    api = HfApi()
    account = api.whoami()['name']
    repo_id = f'{account}/{args.name}'
    url = api.create_repo(
        repo_id,
        repo_type='space',
        space_sdk='gradio',
        space_hardware=SpaceHardware.ZERO_A10G,
        private=False,
        exist_ok=False,
    )
    print(f'Space criado em {url}', flush=True)
    commit = api.upload_folder(
        repo_id=repo_id,
        repo_type='space',
        folder_path=Path(__file__).with_name('space'),
        ignore_patterns=['__pycache__/*', '**/__pycache__/*', '*.pyc'],
        commit_message='Publish Liquid Sense ZeroGPU prototype',
    )
    print(f'Código publicado em {commit.commit_url}', flush=True)


if __name__ == '__main__':
    main()
