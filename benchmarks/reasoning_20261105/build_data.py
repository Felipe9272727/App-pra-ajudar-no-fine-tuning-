"""Pinned official-source, deterministic subsets; never imported by generation."""
import base64
import hashlib
import io
import json
import pickle
import re
import zlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
SEED='2026110501'


class DataOnlyUnpickler(pickle.Unpickler):
    def find_class(self,module,name):
        raise pickle.UnpicklingError('No executable/global objects in benchmark data')


def private_cases(encoded):
    try:
        return json.loads(encoded)
    except json.JSONDecodeError:
        obj=zlib.decompressobj()
        raw=obj.decompress(base64.b64decode(encoded),64*1024*1024+1)
        if len(raw)>64*1024*1024 or obj.unconsumed_tail:
            raise ValueError('Private test expansion too large')
        payload=DataOnlyUnpickler(io.BytesIO(raw)).load()
        return json.loads(payload) if isinstance(payload,(str,bytes)) else payload


def order(value):
    return hashlib.sha256((SEED+':'+str(value)).encode()).hexdigest()


def main():
    assert not (HERE/'prompts.json').exists(),'Subset already fixed; do not rebuild after outputs'
    prompts=[];oracles={};selected={}
    lcb=[json.loads(x) for x in (HERE/'lcb_v6.jsonl').open()]
    eligible=[r for r in lcb if r['difficulty']=='easy' and r['platform']=='atcoder'
              and not json.loads(r['metadata']).get('func_name')]
    chosen=sorted(eligible,key=lambda r:order(r['question_id']))[:8]
    selected['lcb']=[r['question_id'] for r in chosen]
    for r in chosen:
        qid='lcb:'+r['question_id']
        statement=re.split(r'(?mi)^\s*#{0,5}\s*(?:sample\s+(?:input|output)|examples?)\b',r['question_content'],maxsplit=1)[0].strip()
        prompt=statement+'\n\nWrite a complete Python 3 program reading standard input and writing standard output. Return only the code. Use only sys, math, collections, itertools, functools, heapq or bisect if imports are needed.'
        prompts.append({'id':qid,'benchmark':'LiveCodeBench-v6-subset','prompt':prompt,'budget':384})
        raw=private_cases(r['private_test_cases']);assert isinstance(raw,list) and raw
        indices=sorted(sorted(range(len(raw)),key=lambda i:order(qid+':'+str(i)))[:16])
        cases=[{'input':raw[i]['input'],'output':raw[i]['output']} for i in indices]
        assert all(isinstance(x['input'],str) and isinstance(x['output'],str) for x in cases)
        oracles[qid]={'cases':cases,'private_case_indices':indices,'total_original_private_cases':len(raw)}
    gsm=[json.loads(x) for x in (HERE/'gsm8k_test.jsonl').open()]
    indices=sorted(range(len(gsm)),key=order)[:16];selected['gsm8k']=indices
    for i in indices:
        r=gsm[i];qid='gsm8k:'+str(i)
        prompts.append({'id':qid,'benchmark':'GSM8K-zero-shot-subset','prompt':r['question']+'\nReturn only the final numeric answer, without an explanation.','budget':64})
        oracles[qid]={'answer':r['answer'].rsplit('####',1)[1].strip()}
    whitelist={'keywords:existence','keywords:forbidden_words','change_case:english_capital',
               'change_case:english_lowercase','startend:end_checker','detectable_format:title',
               'detectable_format:json_format','detectable_format:multiple_sections',
               'detectable_format:number_bullet_lists'}
    ifrows=[json.loads(x) for x in (HERE/'vendor/instruction_following_eval/data/input_data.jsonl').open()]
    eligible=[r for r in ifrows if len(r['instruction_id_list'])==1
              and r['instruction_id_list'][0] in whitelist and len(r['prompt'])<=1000]
    assert len(eligible)>=12
    chosen=sorted(eligible,key=lambda r:order(r['key']))[:12]
    selected['ifeval']=[r['key'] for r in chosen]
    for r in chosen:
        qid='ifeval:'+str(r['key'])
        prompts.append({'id':qid,'benchmark':'IFEval-filtered-subset','prompt':r['prompt'],'budget':192})
        oracles[qid]=r
    for name,data in [('prompts.json',prompts),('oracles.json',oracles),('selected_ids.json',selected)]:
        (HERE/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    sources={'lcb':{'url':'https://huggingface.co/datasets/livecodebench/code_generation_lite','revision':'0fe84c3912ea0c4d4a78037083943e8f0c4dd505','file':'test6.jsonl','sha256':hashlib.sha256((HERE/'lcb_v6.jsonl').read_bytes()).hexdigest()},
        'gsm8k':{'url':'https://github.com/openai/grade-school-math','revision':'3101c7d5072418e28b9008a6636bde82a006892c','file':'grade_school_math/data/test.jsonl','sha256':hashlib.sha256((HERE/'gsm8k_test.jsonl').read_bytes()).hexdigest()},
        'ifeval':{'url':'https://github.com/google-research/google-research/tree/master/instruction_following_eval','revision':(HERE/'ifeval_revision.txt').read_text().strip()},
        'vendor_usage':[{'url':'https://huggingface.co/LiquidAI/LFM3-1.7B','benchmarks':['LiveCodeBench v6','IFEval']},{'url':'https://www.liquid.ai/blog/lfm2-5-1-2b-thinking-on-device-reasoning-under-1gb','benchmarks':['GSM8K']}],
        'seed':SEED,'sizes':{'lcb':8,'gsm8k':16,'ifeval':12},'selection_before_outputs':True}
    (HERE/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
    print('BENCHMARK_SUBSETS_FIXED',selected)


if __name__=='__main__':main()
