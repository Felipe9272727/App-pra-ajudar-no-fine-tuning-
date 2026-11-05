"""Previously missing original baseline on the identical16-task development set."""
from run import *

@torch.inference_mode()
def main():
    verify();path=HERE/'development_original.json'
    report=json.loads(path.read_text()) if path.exists() else {'variant':'original','status':'running','rows':[],
        'controls':[],'purpose':'observed development comparison, never a fresh final',
        'protocol':{'coding_max_tokens':160,'control_max_tokens':32,'greedy':True,'thinking':False,
            'threads':4,'cache':True,'precision':'BF16','attention':'eager','reference_answers_in_prompt':False}}
    if report['status']=='complete':return
    status(status='original_development_comparison',model_process_active=True)
    model,meta=e.cr.load('original');tok=e.cr.tokenizer();report['model']=meta
    for task in e.DATA['search']+e.DATA['guard']:
        if task['id'] not in {r['id'] for r in report['rows']}:
            report['rows']+=e.coding(model,tok,[task]);save(path.name,report)
    for row in e.DATA['search_controls']:
        if row['id'] not in {r['id'] for r in report['controls']}:
            report['controls']+=e.quality(model,tok,[row]);save(path.name,report)
    report['control_bits']=[r['correct'] for r in report['controls']]
    report['anchor_nll']=e.cr.likelihood(model,tok,e.DATA['anchors'],anchors=True)['mean_nll']
    report['status']='complete';save(path.name,report)
    status(status='original_development_complete',model_process_active=False)
    print('ORIGINAL_DEVELOPMENT_COMPLETE',sum(r['passed'] for r in report['rows']),flush=True)

if __name__=='__main__':main()
