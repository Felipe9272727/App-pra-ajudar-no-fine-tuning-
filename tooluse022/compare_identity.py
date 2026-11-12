"""Same user question, fixed192tokens, before any new tool-use training."""
import sys,json,time,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse022';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
import train_runtime as tr
QUESTION='Eai mano quem é você, e você é melhor que os melhores modelos?'
@tr.torch.inference_mode()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('variant',choices=['original','general','specialist','original_app_system']);a=ap.parse_args();path=HERE/'comparisons'/(a.variant+'.json');assert not path.exists(),'Do not rerun completed comparison'
 if a.variant in ['original','original_app_system']:model,meta=tr.e.cr.load('original');tok=tr.e.cr.tokenizer()
 elif a.variant=='general':model,tok,parent,meta=tr.load();del parent
 else:
  from supervised015.attempt_e.restore import load_d
  model,tok,meta,ck=load_d();assert ck['stream_sha256']=='33f4d2b0fa0d36329ec0bd59d94ca9054c5c4ab549b7a551743a955711679b85'
 messages=[{'role':'user','content':QUESTION}];system=''
 if a.variant=='original_app_system':system=json.loads((ROOT/'model_identity.json').read_text())['system_message'];messages.insert(0,{'role':'system','content':system})
 ids=tok.apply_chat_template(messages,tokenize=True,return_tensors='pt',return_dict=False,add_generation_prompt=True,enable_thinking=False);tr.torch.manual_seed(0);start=time.monotonic();out=model.generate(input_ids=ids,max_new_tokens=192,do_sample=False,use_cache=True,pad_token_id=tok.eos_token_id)[0,ids.shape[1]:];text=tok.decode(out,skip_special_tokens=True)
 report={'variant':a.variant,'question':QUESTION,'input_ids_sha256':hashlib.sha256(ids.numpy().tobytes()).hexdigest(),'system_message':system,'protocol':{'thinking':False,'greedy':True,'seed':0,'max_new_tokens':192,'cpu_threads':4,'framework':'PyTorch2.15CPU','same_neutral_inputs_for_first_three_variants':a.variant!='original_app_system','no_reference_answer_in_input':True,'new_training_updates':0,'hardware_not_Android':True},'output':text,'new_tokens':len(out),'hit_limit':len(out)==192,'seconds_descriptive_only':time.monotonic()-start,'source_metadata':meta,'not_a_benchmark_or_general_superiority_test':True}
 tr.e.cr.atomic_json(path,report);print(json.dumps({'variant':a.variant,'output':text,'new_tokens':len(out),'hit_limit':report['hit_limit']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
