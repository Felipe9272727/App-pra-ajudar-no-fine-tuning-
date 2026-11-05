"""Extend every unfinished thinking diagnostic under a preregistered cap."""
from run import *

@torch.inference_mode()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('variant',choices=['original','liquid']);a=parser.parse_args()
    verify();baseline=json.loads((HERE/f'thinking_{a.variant}.json').read_text());assert baseline['status']=='complete'
    path=HERE/f'thinking1024_{a.variant}.json'
    report=json.loads(path.read_text()) if path.exists() else {'variant':a.variant,'status':'running','rows':[],
        'purpose':'observed paired output-budget diagnostic; not weight validation',
        'protocol':{'thinking':True,'greedy':True,'max_new_tokens':1024,'seed':0,'threads':4}}
    if report['status']=='complete':return
    model=None;tok=None
    bank={x['id']:x for x in json.loads((ROOT/'benchmarks/reasoning_20261105/prompts.json').read_text())}
    oracles=json.loads((ROOT/'benchmarks/reasoning_20261105/oracles.json').read_text())
    status(status='budget1024_'+a.variant,model_process_active=True)
    for old in [r for r in baseline['rows'] if r['thinking']]:
        if old['id'] in {r['id'] for r in report['rows']}:continue
        if not old['hit_limit']:
            row={**old,'reused_completed_512_output':True,'seconds_additional':0.,'same_512_prefix':True}
        else:
            if model is None:
                model,meta=e.cr.load('original' if a.variant=='original' else 'baseline');tok=e.cr.tokenizer()
                if a.variant=='liquid':apply(model,e.read_checkpoint('best.pt'))
            task=bank[old['id']];ids=e.cr.prompt(tok,task['prompt'],thinking=True);torch.manual_seed(0)
            started=time.monotonic()
            output=model.generate(input_ids=ids,max_new_tokens=1024,use_cache=True,
                do_sample=False,pad_token_id=tok.eos_token_id)[0,ids.shape[1]:]
            text=tok.decode(output,skip_special_tokens=True)
            prefix=tok.decode(output[:512],skip_special_tokens=True)
            assert prefix==old['output'],'A new cap must preserve the earlier generated prefix'
            score=public.grade(task,text,oracles[old['id']])
            row={'id':old['id'],'thinking':True,'output':text,'new_tokens':len(output),
                'hit_limit':len(output)==1024,'thinking_closed':'</think>' in text,
                'reused_completed_512_output':False,'same_512_prefix':True,
                'token_ids':output.tolist(),'seconds_additional':time.monotonic()-started,**score}
        report['rows'].append(row);save(path.name,report)
        print('BUDGET1024',a.variant,row['id'],row['new_tokens'],row['passed'],row['thinking_closed'],flush=True)
    report['status']='complete';save(path.name,report)
    status(status='budget1024_complete_'+a.variant,model_process_active=False)

if __name__=='__main__':main()
