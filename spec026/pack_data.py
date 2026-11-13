"""Full-conversation causal-LM blocks for from-scratch training; no evaluation data."""
import hashlib,json,torch
from pathlib import Path
from transformers import AutoTokenizer
from io_parts import save_json,file_hash
H=Path(__file__).resolve().parent;ROOT=H.parent

def main():
 cfg=json.loads((H/'config.json').read_text());tok=AutoTokenizer.from_pretrained(ROOT/'upstream',local_files_only=True);correct=json.loads((H/'data/correct_train.json').read_text());teacher=json.loads((H/'data/teacher_traces.json').read_text());assert len(teacher)==24;stream=[];samples=[]
 for r in correct:
  p=tok.apply_chat_template([{'role':'user','content':r['prompt']}],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=False);a=tok.encode(r['answer'],add_special_tokens=False)+[248046];stream+=p+a;samples.append({'id':r['id'],'source':r['source'],'prompt_tokens':len(p),'answer_tokens':len(a)})
 for r in teacher:
  a=list(r['answer_ids']);added=not a or a[-1] not in [248044,248046]
  if added:a.append(248046)
  stream+=r['prompt_ids']+a;samples.append({'id':r['id'],'source':'actual_teacher_behavior','prompt_tokens':len(r['prompt_ids']),'answer_tokens':len(a),'artificial_document_boundary_after_truncated_trace':added})
 assert min(stream)>=0 and max(stream)<248320;n=cfg['block_tokens'];xs=[];ys=[]
 for start in range(0,len(stream)-1,n):
  chunk=stream[start:start+n+1];length=len(chunk);chunk+= [248046]*(n+1-length);xs.append(chunk[:-1]);ys.append([chunk[i+1] if i+1<length else -100 for i in range(n)])
 data={'input_ids':torch.tensor(xs),'labels':torch.tensor(ys)};p=H/'data/packed.pt.bin';assert not p.exists();torch.save(data,p);tokens=int((data['labels']!=-100).sum());steps=(len(xs)+cfg['batch_size']-1)//cfg['batch_size']*cfg['epochs'];save_json(H/'data/packed_manifest.json',{'format':'full-conversation-causal-LM-blocks-v1','samples':samples,'unique_conversations':len(samples),'raw_stream_tokens':len(stream),'label_tokens_per_epoch':tokens,'training_token_presentations_per_size':tokens*cfg['epochs'],'blocks':len(xs),'block_tokens':n,'batch_size':cfg['batch_size'],'epochs':cfg['epochs'],'optimizer_steps_per_size':steps,'training_labels_include_user_text':True,'teacher_traces_not_verified_solutions':True,'quality_or_speed_data_included':False,'packed_sha256':file_hash(p)});print('PACKED',len(xs),tokens,steps,flush=True)
if __name__=='__main__':main()
