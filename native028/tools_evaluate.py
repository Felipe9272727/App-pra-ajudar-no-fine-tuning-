"""Two identical Python-only probes per variant with genuine executor results."""
import argparse,re
from inference import *
from tooluse022.tools import parse_call,execute,call_text


def main(variant):
    verify_stage('evaluation');name=f'reports/tools_{variant}.json'
    report=read(name) if (H/name).exists() else {'variant':variant,'rows':[],
        'scope':'two descriptive Python probes; nonthinking, 128tokens/turn, three turns, at most two calls; no web',
        'system_same_as_training':True}
    if report.get('status')=='complete':return
    m,tok,meta=load_variant(variant);report['metadata']=meta
    system=read('data/train_tools.json')[0]['messages'][0]
    schemas=read('data/schemas.json')
    for row in read('data/tool_probes.json'):
        if row['id'] in {r['id'] for r in report['rows']}:continue
        messages=[system,{'role':'user','content':row['prompt']}];observations=[];turns=[];calls=0
        if 'prior_failed_call' in row:
            text=call_text('run_python','code',row['prior_failed_call']);obs=execute({'name':'run_python','arguments':{'code':row['prior_failed_call']}})
            observations.append({'origin':'fixed_probe_prior_error','observation':obs})
            messages.extend([{'role':'assistant','content':text},{'role':'tool','content':json.dumps({k:v for k,v in obs.items() if k in ['tool','ok','stdout','error']},ensure_ascii=False)}])
        final='';error=None
        for turn in range(3):
            out=generate(m,tok,row,False,128,messages=messages,tools=schemas);turns.append(out)
            try:call=parse_call(out['delivered'])
            except (ValueError,AssertionError) as exc:error=str(exc);break
            if call is None:final=out['delivered'];break
            if call['name']!='run_python' or calls>=2:error='unsupported call or two-call limit';break
            obs=execute(call);calls+=1;observations.append({'origin':'model_call','call':call,'observation':obs})
            messages.extend([{'role':'assistant','content':out['delivered']},
                {'role':'tool','content':json.dumps({k:v for k,v in obs.items() if k in ['tool','ok','stdout','error']},ensure_ascii=False)}])
        numeric=bool(re.fullmatch(r'[-+]?\d+(?:\.\d+)?',final.strip()))
        correct=numeric and float(final.strip())==float(row['expected'])
        success=correct and any(x['origin']=='model_call' and x['observation'].get('ok') for x in observations)
        r={'id':row['id'],'turns':turns,'observations':observations,'messages':messages,'final':final,
            'actual_model_calls':calls,'parse_error':error,'numeric_answer_correct':correct,'tool_success':success}
        report['rows'].append(r);save(name,report);print('TOOL028',variant,row['id'],calls,success,flush=True)
    report['status']='complete';report['successes']=sum(r['tool_success'] for r in report['rows']);save(name,report)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('variant',choices=['original','parent','sft_final','policy_final']);a=ap.parse_args();main(a.variant)
