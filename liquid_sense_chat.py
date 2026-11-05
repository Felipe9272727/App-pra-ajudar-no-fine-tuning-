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


def display_answer(text):
    """Display the final segment if the model emits a literal reasoning marker."""
    return (text.rsplit('</think>',1)[1] if '</think>' in text else text).strip()


def main():
    p=argparse.ArgumentParser();p.add_argument('--message');p.add_argument('--about',action='store_true')
    p.add_argument('--thinking',action='store_true',help='Ativa o raciocínio nativo experimental; usa mais tokens.')
    p.add_argument('--max-new-tokens',type=int,default=None);a=p.parse_args()
    budget=a.max_new_tokens if a.max_new_tokens is not None else (1024 if a.thinking else 256)
    info=profile()
    if a.about:
        print(info['presentation']);return
    with contextlib.redirect_stdout(sys.stderr):
        from runtime_helpers import load,apply,e,torch,PARENT_HASH
    assert 1<=budget<=1024
    with contextlib.redirect_stdout(sys.stderr):
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
                                        add_generation_prompt=True,enable_thinking=a.thinking)
            if ids.shape[1]<=2048 or len(messages)<=2:break
            del messages[1:3]
        torch.manual_seed(0)
        with torch.inference_mode():
            output=model.generate(input_ids=ids,max_new_tokens=budget,use_cache=True,do_sample=False,
                                  pad_token_id=tok.eos_token_id)[0,ids.shape[1]:]
        raw=tok.decode(output,skip_special_tokens=True)
        if a.thinking and ('</think>' not in raw or not raw.rsplit('</think>',1)[-1].strip()):
            print('O Liquid Sense não concluiu uma resposta dentro deste orçamento de tokens.',flush=True)
            messages.pop()
            if a.message is not None:break
            continue
        answer=display_answer(raw)
        print(answer,flush=True);messages.append({'role':'assistant','content':answer})
        if a.message is not None:break


if __name__=='__main__':main()
