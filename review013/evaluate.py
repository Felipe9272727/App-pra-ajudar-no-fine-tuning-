"""Matched free-generation screen, controls, and gated reserved evaluation."""
import argparse,time
from review_runtime import *

@torch.inference_mode()
def run(kind,phase):
    verify_frozen();model,tok,meta,installed=load_variant(kind)
    dest=HERE/(phase+'_'+kind+'.json')
    patch_hash=meta.get('adapter_sha256')
    report=json.loads(dest.read_text()) if dest.exists() else {'kind':kind,'phase':phase,'metadata':meta,'rows':[],
       'protocol':{'max_new_tokens':160,'do_sample':False,'seed':0,'thinking':False,'threads':4,'solutions_or_cases_in_prompt':False}}
    assert report['metadata'].get('adapter_sha256')==patch_hash
    if phase=='screen':
        rows=[r for r in json.loads((HERE/'validation.json').read_text()) if r['variant'] in [0,9]]
    elif phase=='full_validation':rows=json.loads((HERE/'validation.json').read_text())
    elif phase=='test':
        decision=json.loads((HERE/'selection.json').read_text());assert decision['eligible_for_final_test']
        assert kind in ['original','parent',decision['selected']]
        rows=json.loads((HERE/'test.json').read_text())
    else:rows=[]
    seen={r['id'] for r in report['rows']}
    if phase=='learning_diagnostic':
        rows=[r for r in json.loads((HERE/'train.json').read_text()) if r['variant'] in [0,9]]
        for row in rows:
            if row['id'] in seen:continue
            ids=e.cr.prompt(tok,row['prompt']);answer=tok.encode(row['solution']+tok.eos_token,add_special_tokens=False)
            joined=torch.cat([ids,torch.tensor([answer])],dim=1)
            out=model(input_ids=joined[:,:-1],use_cache=False,logits_to_keep=len(answer))
            logits=out.logits[0].float();gold=torch.tensor(answer)
            report['rows'].append({'id':row['id'],'nll':float(torch.nn.functional.cross_entropy(logits,gold)),
                       'token_accuracy':float((logits.argmax(-1)==gold).float().mean()),'tokens':len(answer)})
            e.cr.atomic_json(dest,report)
            print('TRAIN_NLL',kind,row['id'],round(report['rows'][-1]['nll'],4),flush=True)
        report['mean_task_nll']=sum(r['nll'] for r in report['rows'])/len(rows)
        report['mean_task_token_accuracy']=sum(r['token_accuracy'] for r in report['rows'])/len(rows)
        report['diagnostic_only']=True
        report['status']='complete';e.cr.atomic_json(dest,report)
        if installed:installed.close()
        return
    if phase=='controls':
        report['language_anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)
    for row in rows:
        if row['id'] in seen:continue
        out=e.cr.generate(model,tok,eval_inputs(row),max_tokens=160);out.pop('trace',None)
        score=evaluate(out['output'],{'cases':row['cases']})
        stats=installed.stats() if installed else None
        report['rows'].append({'id':row['id'],'family':row['family'],**out,**score,'mechanism':stats})
        e.cr.atomic_json(dest,report)
        print('EVAL',phase,kind,row['id'],score['passed'],score['total'],round(out['seconds'],2),flush=True)
    if phase=='controls':
        controls=json.loads((HERE/'controls.json').read_text())
        for row in controls:
            if row['id'] in seen:continue
            out=e.cr.generate(model,tok,row['question'],max_tokens=64);out.pop('trace',None)
            ok,_=e.cr.grade(out['output'],row)
            report['rows'].append({'id':row['id'],**out,'correct':ok})
            e.cr.atomic_json(dest,report)
            print('CONTROL',kind,row['id'],ok,flush=True)
    report['status']='complete';report['total']=len(report['rows'])
    if phase=='controls':report['correct']=sum(r['correct'] for r in report['rows'])
    else:
        report['tasks_passed']=sum(r['all_passed'] for r in report['rows'])
        report['cases_passed']=sum(r['passed'] for r in report['rows'])
        report['cases_total']=sum(r['total'] for r in report['rows'])
    e.cr.atomic_json(dest,report)
    if installed:installed.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['original','parent','loop','joint']);p.add_argument('phase',choices=['screen','controls','full_validation','test','learning_diagnostic']);args=p.parse_args();run(args.kind,args.phase)
