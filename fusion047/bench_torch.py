"""Run frozen prompts with the CPU or CUDA port, with or without the identity weights."""
import argparse
import json
from pathlib import Path

import torch

from torch_runtime import LiquidSenseTorch

PARENT_ADAPTER = '941daca310736af121cdd337317b5e1bddb741b88ea085d684d3760ecc1fecfd'


def main(args):
    torch.set_num_threads(2)
    model = LiquidSenseTorch(args.checkpoint,args.adapter,PARENT_ADAPTER,args.device,
                             identity=args.head,identity_sha=args.head_sha)
    prompts = json.loads(args.prompts.read_text())
    with args.output.open('w') as result:
        for prompt in prompts:
            answer = model.generate(prompt['prompt'], **prompt['options'])
            row = {'id':prompt['id'], 'group':prompt['group'], 'seconds':answer['seconds'],
                   'answer':answer}
            print(json.dumps(row,ensure_ascii=False),file=result,flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('checkpoint','adapter','prompts','output'):
        parser.add_argument(name,type=Path)
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--head', type=Path)
    parser.add_argument('--head-sha')
    main(parser.parse_args())
