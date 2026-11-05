"""Matched benchmark generation: hidden oracles are used only after decoding."""
import argparse
import hashlib
import json
import re
import random
import sys
import time
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import e,torch,apply,PARENT_HASH
import stdio_judge
sys.path.insert(0,str(HERE/'vendor'))
from instruction_following_eval import evaluation_lib as ifeval


def grade_number(output, expected):
    text=output.strip()
    if '</think>' in text:text=text.rsplit('</think>',1)[1].strip()
    if not text:return False
    line=text.splitlines()[-1].strip()
    if '####' in line:line=line.rsplit('####',1)[1]
    if re.search(r'(?i)answer\s*:',line):line=re.split(r'(?i)answer\s*:',line)[-1]
    line=line.strip(' `')
    if line.endswith('.'):line=line[:-1]
    values=re.findall(r'(?<![\w.])-?(?:\d[\d,]*(?:\.\d+)?|\.\d+)(?:/\d+)?(?![\w.])',line)
    if len(values)!=1:return False
    try:return Fraction(values[0].replace(',',''))==Fraction(expected.replace(',',''))
    except (ValueError,ZeroDivisionError):return False


def grade(task, output, oracle):
    if task['id'].startswith('lcb:'):
        return stdio_judge.evaluate(output,oracle)
    if task['id'].startswith('gsm8k:'):
        ok=grade_number(output,oracle['answer'])
        return {'all_passed':ok,'passed':int(ok),'total':1,'case_passed':[ok]}
    inp=ifeval.InputExample(key=oracle['key'],instruction_id_list=oracle['instruction_id_list'],prompt=oracle['prompt'],kwargs=oracle['kwargs'])
    random.seed(0);strict=ifeval.test_instruction_following_strict(inp,{inp.prompt:output})
    random.seed(0);loose=ifeval.test_instruction_following_loose(inp,{inp.prompt:output})
    bits=strict.follow_instruction_list
    return {'all_passed':strict.follow_all_instructions,'passed':sum(bits),'total':len(bits),'case_passed':bits,
            'loose_all_passed':loose.follow_all_instructions,'instruction_ids':oracle['instruction_id_list']}


@torch.inference_mode()
def identity_probe(model,tok):
    info=json.loads((ROOT/'model_identity.json').read_text())
    question='Quem é você e quem desenvolveu você? Responda em um parágrafo curto.'
    ids=tok.apply_chat_template([{'role':'system','content':info['system_message']},{'role':'user','content':question}],
        tokenize=True,return_tensors='pt',return_dict=False,add_generation_prompt=True,enable_thinking=False)
    torch.manual_seed(0)
    tokens=model.generate(input_ids=ids,max_new_tokens=160,use_cache=True,do_sample=False,pad_token_id=tok.eos_token_id)[0,ids.shape[1]:]
    text=tok.decode(tokens,skip_special_tokens=True)
    result={'mechanism':'branded application system message; not raw weight identity',
            'question':question,'output':text,'new_tokens':len(tokens),
            'contains_liquid_sense':'liquid sense' in text.casefold(),'mentions_qwen':'qwen' in text.casefold(),
            'excluded_from_capability_scores':True}
    e.cr.atomic_json(ROOT/'reasoning/identity_probe.json',result)


@torch.inference_mode()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('variant',choices=['original','liquid','parent']);a=parser.parse_args()
    frozen=json.loads((HERE/'frozen.json').read_text())
    assert a.variant in frozen['variants']
    for name,digest in frozen['files'].items():assert e.cr.file_hash(ROOT/name)==digest,name
    selection=json.loads((ROOT/'reasoning/selection.json').read_text())
    assert e.cr.file_hash(ROOT/'reasoning/selection.json')==frozen['selection_sha256']
    rows=json.loads((HERE/'prompts.json').read_text());oracles=json.loads((HERE/'oracles.json').read_text())
    path=HERE/f'results_{a.variant}.json';fingerprint=e.cr.file_hash(HERE/'frozen.json')
    report=json.loads(path.read_text()) if path.exists() else {'variant':a.variant,'status':'running','rows':[],
        'frozen_sha256':fingerprint,'branding_in_benchmark':False,'no_reference_answers_in_generation':True,
        'backward_passes':0,'matched_protocol':{'greedy':True,'thinking':False,'cpu_threads':4,'cache':True,'precision':'BF16','attention':'eager'}}
    assert report['frozen_sha256']==fingerprint
    model,meta=e.cr.load('original' if a.variant=='original' else 'baseline');tok=e.cr.tokenizer()
    if a.variant!='original':
        parent=torch.load(ROOT/'rsi100/checkpoints/best.pt',weights_only=True)
        assert e.cr.file_hash(ROOT/'rsi100/checkpoints/best.pt')==PARENT_HASH
        patch=None
        if a.variant=='liquid' and selection.get('patch'):
            pp=ROOT/selection['patch'];assert e.cr.file_hash(pp)==selection['patch_sha256']
            patch=torch.load(pp,weights_only=True)
        meta['architecture']=apply(model,parent,patch)
    report['model']=meta
    report['runtime']={'torch':torch.__version__,'cpu_quota':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'threads':torch.get_num_threads()}
    seen={r['id'] for r in report['rows']}
    for task in rows:
        if task['id'] in seen:continue
        generated=e.cr.generate(model,tok,task['prompt'],max_tokens=task['budget']);generated.pop('trace')
        result=grade(task,generated['output'],oracles[task['id']])
        report['rows'].append({'id':task['id'],'benchmark':task['benchmark'],
            'prompt_sha256':hashlib.sha256(task['prompt'].encode()).hexdigest(),**generated,**result})
        e.cr.atomic_json(path,report)
        print('PUBLIC_BENCH',a.variant,task['id'],result['passed'],result['total'],generated['new_tokens'],flush=True)
    report.update(status='complete',completed_unix=time.time());e.cr.atomic_json(path,report)
    if a.variant=='liquid' and not (ROOT/'reasoning/identity_probe.json').exists():identity_probe(model,tok)
    print('PUBLIC_VARIANT_COMPLETE',a.variant,flush=True)


if __name__=='__main__':main()
