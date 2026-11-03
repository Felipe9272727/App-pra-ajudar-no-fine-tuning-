"""Load the final active hybrid and optionally apply the frozen dense edit."""
import argparse
import json
from common import *


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--question',required=True)
    parser.add_argument('--max-new-tokens',type=int,default=128)
    args=parser.parse_args()
    assert 1<=args.max_new_tokens<=512
    frozen=json.loads((HERE/'frozen.json').read_text())
    assert frozen['recipe']==RECIPE and frozen['data_sha256']==DATA_HASH
    assert file_hash(ROOT/'checkpoints/liquid_patch.pt')==frozen['liquid_patch_sha256']
    model=load_hybrid()
    if frozen['patch']:
        assert file_hash(ROOT/frozen['patch'])==frozen['patch_sha256']
        apply_edit(model,ROOT/frozen['patch'])
    print(json.dumps({'model':model.config.model_name,'architecture':architecture_check(model)}),flush=True)
    tok=tokenizer();ids=prompt_ids(tok,args.question)
    output=model.generate(input_ids=ids,max_new_tokens=args.max_new_tokens,
        do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id)
    print(tok.decode(output[0,ids.shape[1]:],skip_special_tokens=True))


if __name__=='__main__':main()
