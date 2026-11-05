"""Honest branded chat; identity configuration is excluded from benchmarks."""
import argparse
import contextlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'reasoning'))


def profile():
    return json.loads((ROOT/'model_identity.json').read_text())


def main():
    p=argparse.ArgumentParser();p.add_argument('--message');p.add_argument('--about',action='store_true')
    p.add_argument('--max-new-tokens',type=int,default=256);a=p.parse_args()
    info=profile()
    if a.about:
        print(info['presentation']);return
    with contextlib.redirect_stdout(sys.stderr):
        from runtime_helpers import load,apply,e,torch,PARENT_HASH
    assert 1<=a.max_new_tokens<=1024
    model,tok,parent,_=load()
    selection_path=ROOT/'reasoning/selection.json'
    if selection_path.exists():
        selected=json.loads(selection_path.read_text())
        if selected.get('patch'):
            patch_path=ROOT/selected['patch'];assert e.cr.file_hash(patch_path)==selected['patch_sha256']
            apply(model,parent,torch.load(patch_path,weights_only=True))
    messages=[{'role':'system','content':info['system_message']}]
    if not a.message:print(info['presentation']+'\nDigite /sair para encerrar.\n')
    while True:
        question=a.message if a.message is not None else input('Você: ')
        if question.strip().casefold() in ['/sair','/exit']:break
        messages.append({'role':'user','content':question})
        while True:
            ids=tok.apply_chat_template(messages,tokenize=True,return_tensors='pt',return_dict=False,
                                        add_generation_prompt=True,enable_thinking=False)
            if ids.shape[1]<=2048 or len(messages)<=2:break
            del messages[1:3]
        torch.manual_seed(0)
        with torch.inference_mode():
            output=model.generate(input_ids=ids,max_new_tokens=a.max_new_tokens,use_cache=True,do_sample=False,
                                  pad_token_id=tok.eos_token_id)[0,ids.shape[1]:]
        answer=tok.decode(output,skip_special_tokens=True)
        print(answer,flush=True);messages.append({'role':'assistant','content':answer})
        if a.message is not None:break


if __name__=='__main__':main()
