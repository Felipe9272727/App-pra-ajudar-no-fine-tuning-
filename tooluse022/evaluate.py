"""Same real-tool agent loop for original Qwen, exactE and learned candidate."""
import argparse,hashlib,json,re,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse022';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
from tooluse022.train import torch,tr,load_e,verify
from tooluse022.tools import parse_call,execute,safe_text
from transformers import StoppingCriteria,StoppingCriteriaList
class EndCall(StoppingCriteria):
 def __init__(self,tok,start):self.tok=tok;self.start=start
 def __call__(self,ids,scores,**kw):return '</tool_call>' in self.tok.decode(ids[0,self.start:],skip_special_tokens=False)
def adapter(model):
 data=torch.load(HERE/'checkpoints/final.pt',weights_only=True);a=data['A'];b=data['B']
 def hook(module,args,h):return (h.float()+torch.nn.functional.linear(torch.nn.functional.linear(h.float(),a),b)).to(h.dtype)
 return model.model.language_model.norm.register_forward_hook(hook)
def grade(row,turns):
 finals=[r['raw'] for r in turns if r.get('call') is None];final=finals[-1] if finals else '';calls=[r for r in turns if r.get('observation')];valid=any(r['observation'].get('ok') for r in calls);kind=row['kind'];correct=False
 if kind=='python':correct=any(r['call']['name']=='run_python' and r['observation'].get('ok') and row['expected'] in r['observation'].get('stdout','') for r in calls) and row['expected'] in final
 else:
  for r in calls:
   obs=r['observation'];q=r['call']['arguments'].get('query','').lower()
   if r['call']['name']=='search_web' and obs.get('ok') and all(t in q for t in row['query_terms']):correct=any(i['url'] in final for i in obs.get('items',[]))
 return {'correct_final_with_real_tool':bool(correct),'actual_tool_calls':len(calls),'successful_tool_call':valid,'final_present':bool(final),'truncated':any(t['new_tokens']==256 for t in turns),'false_tool_claim_audit_required':True}
@torch.inference_mode()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('variant',choices=['original','specialist','candidate']);ap.add_argument('--set',choices=['fresh','teach'],default='fresh');args=ap.parse_args();verify();p=HERE/'results'/f'{args.set}_{args.variant}.json';results=json.loads(p.read_text()) if p.exists() else [];config=json.loads((HERE/'tool_config.json').read_text())
 if args.variant=='original':model,meta=tr.e.cr.load('original');tok=tr.e.cr.tokenizer()
 else:model,tok,meta=load_e()
 handle=adapter(model) if args.variant=='candidate' else None
 rows=json.loads((HERE/'fresh.json').read_text())
 if args.set=='teach':
  train=json.loads((HERE/'train.json').read_text());rows=[]
  for item in train[::2]:
   obs=json.loads(next(r for r in train if r['id']==item['id']+'_final')['messages'][-1]['content']);q=item['messages'][-1]['content'];rows.append({'id':item['id'],'question':q,'kind':item['kind'],'expected':obs.get('stdout','').strip(),'query_terms':[]})
 for row in rows:
  if any(r['id']==row['id'] for r in results):continue
  messages=[{'role':'system','content':config['system']},{'role':'user','content':row['question']}];turns=[];start=time.monotonic()
  for turn in range(3):
   ids=tok.apply_chat_template(messages,tools=config['schemas'],add_generation_prompt=True,enable_thinking=False,return_dict=False,return_tensors='pt')
   if ids.shape[1]+256>4096:turns.append({'raw':'','error':'context limit','new_tokens':0});break
   torch.manual_seed(0);out=model.generate(input_ids=ids,max_new_tokens=256,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id,stopping_criteria=StoppingCriteriaList([EndCall(tok,ids.shape[1])]))[0,ids.shape[1]:];raw=tok.decode(out,skip_special_tokens=False).removesuffix(tok.eos_token).strip();entry={'turn':turn,'raw':raw,'generated_ids':out.tolist(),'new_tokens':len(out),'input_sha256':hashlib.sha256(ids.numpy().tobytes()).hexdigest()}
   try:call=parse_call(raw);entry['call']=call
   except Exception as e:entry['parse_error']=str(e);turns.append(entry);break
   if call is None:turns.append(entry);break
   if turn==2:entry['error']='tool call limit';turns.append(entry);break
   obs=execute(call);entry['observation']=obs;turns.append(entry);messages.extend([{'role':'assistant','content':raw},{'role':'tool','content':json.dumps(obs,ensure_ascii=False,separators=(',',':'))}])
  result={'id':row['id'],'question':row['question'],'variant':args.variant,'set':args.set,'turns':turns,'grade':grade(row,turns),'seconds':time.monotonic()-start,'reference_answers_or_tests_in_prompt':False};results.append(result);p.parent.mkdir(exist_ok=True);tr.e.cr.atomic_json(p,results);print('EVALUATED',args.variant,row['id'],json.dumps(result['grade']),flush=True)
 if handle:handle.remove()
if __name__=='__main__':main()
