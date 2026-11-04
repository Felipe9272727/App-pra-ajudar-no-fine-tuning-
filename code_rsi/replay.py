"""Replay the frozen coding checkpoint without adaptation or tests."""
import argparse
from runtime import *
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--question',required=True);p.add_argument('--tokens',type=int,default=160);a=p.parse_args()
    f=json.loads((HERE/'frozen.json').read_text())
    assert f['data_sha256']==DATA_HASH
    variant=f['selected'] or 'baseline'
    model,meta=load(variant)
    if f['selected']:assert meta['patch_sha256']==f['selected_patch_sha256']
    print(generate(model,tokenizer(),a.question,max_tokens=a.tokens)['output'])
