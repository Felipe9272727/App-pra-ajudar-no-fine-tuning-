"""One declared1024-token teaching diagnostic; cannot reopen promotion."""
import sys,json,time,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'reasoning018';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
from reasoning018.restore import load_candidate
from local_cpu.sandbox import evaluate as judge
@tr.torch.inference_mode()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('variant',choices=['parent','candidate','original']);a=parser.parse_args();path=HERE/('long1024_'+a.variant+'.json');assert not path.exists(),'Do not repeat completed diagnostic'
 old=json.loads((HERE/('evaluation_'+a.variant+'.json')).read_text());entry=next(r for r in old['code'] if r['id']=='above_0')
 if not entry['hit_limit']:
  result={**entry,'variant':a.variant,'effective_budget':1024,'reused_eos_finished256_run':True,'reused_source':'evaluation_'+a.variant+'.json','selection_allowed':False};tr.e.cr.atomic_json(path,result);return
 if a.variant=='candidate':model,tok,meta,audit=load_candidate()
 elif a.variant=='parent':model,tok,parent,meta=tr.load();del parent
 else:model,meta=tr.e.cr.load('original');tok=tr.e.cr.tokenizer()
 row=next(r for r in json.loads((HERE/'code_train.json').read_text()) if r['id']=='above_0');ids=tr.e.cr.prompt(tok,row['prompt'],thinking=True);tr.torch.manual_seed(0);start=time.monotonic();output=model.generate(input_ids=ids,max_new_tokens=1024,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id)[0,ids.shape[1]:]
 prefix=tok.decode(output[:256],skip_special_tokens=True);assert hashlib.sha256(prefix.encode()).hexdigest()==entry['raw_output_sha256'],'Changed prefix; stop and investigate'
 raw=tok.decode(output,skip_special_tokens=True);closed='</think>' in raw;final=raw.rsplit('</think>',1)[-1].strip() if closed else '';score=judge(final,row)
 result={'id':row['id'],'variant':a.variant,'effective_budget':1024,'greedy':True,'thinking':True,'seed':0,'threads':4,'solutions_in_inputs':False,'selection_allowed':False,'first256_digest_matches_prior_run':True,'reused_eos_finished256_run':False,'final_output':final,'thinking_closed':closed,'has_final':bool(final),'new_tokens':len(output),'hit_limit':len(output)==1024,'seconds':time.monotonic()-start,'raw_output_sha256':hashlib.sha256(raw.encode()).hexdigest(),**score};tr.e.cr.atomic_json(path,result);print('LONG018',a.variant,result['new_tokens'],result['all_passed'],closed,flush=True)
if __name__=='__main__':main()
