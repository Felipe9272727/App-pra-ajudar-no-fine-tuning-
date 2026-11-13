"""Check HF templates without model inference; distinguish observed native checks."""
import hashlib,json,os
os.environ['USE_TORCH']='0';os.environ['USE_TF']='0'
from pathlib import Path
from transformers import AutoTokenizer
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'android_thinking024';tok=AutoTokenizer.from_pretrained(ROOT/'upstream',local_files_only=True);cfg=json.loads((ROOT/'tooluse022/tool_config.json').read_text());prefix=(ROOT/'tooluse022/tools_prefix.txt').read_text()
def render(messages,thinking):
 s=prefix;last=max((i for i,m in enumerate(messages) if m['role']=='user'),default=0)
 for i,m in enumerate(messages):
  c=m['content'].strip();role=m['role']
  if role=='tool':s+=f'<|im_start|>user\n<tool_response>\n{c}\n</tool_response><|im_end|>\n'
  elif role=='assistant':
   r=''
   if '</think>' in c:r,c=c.split('</think>',1);r=r.split('<think>')[-1].strip();c=c.strip()
   s+=f'<|im_start|>assistant\n<think>\n{r}\n</think>\n\n{c}<|im_end|>\n' if i>last else f'<|im_start|>assistant\n{c}<|im_end|>\n'
  else:s+=f'<|im_start|>{role}\n{c}<|im_end|>\n'
 return s+('<|im_start|>assistant\n<think>\n' if thinking else '<|im_start|>assistant\n<think>\n\n</think>\n\n')
fixtures=[f['messages'] for f in json.loads((ROOT/'tooluse022/reports/tool_template_fixtures.json').read_text())]
fixtures.append([{'role':'user','content':'Olá'},{'role':'assistant','content':'<think>old reasoning</think>Olá.'},{'role':'user','content':'Agora confira 7 vezes 8.'}]);rows=[]
for i,m in enumerate(fixtures):
 for thinking in [False,True]:
  hf=tok.apply_chat_template([{'role':'system','content':cfg['system']}]+m,tools=cfg['schemas'],tokenize=False,add_generation_prompt=True,enable_thinking=thinking)
  actual=render(m,thinking);assert hf==actual,(i,thinking)
  rows.append({'fixture':i,'thinking':thinking,'template_match':True,'prompt_sha256':hashlib.sha256(hf.encode()).hexdigest()})
math=json.loads((HERE/'fixtures/arithmetic.json').read_text());expected={}
for mode in [False,True]:
 ids=tok.apply_chat_template([{'role':'system','content':cfg['system']}]+math,tools=cfg['schemas'],tokenize=True,return_dict=False,add_generation_prompt=True,enable_thinking=mode);expected[str(mode)]=len(ids)
# Smallest total prompt above the old2048native hard guard.
msg='Contexto neutro para teste de limite; não é instrução.\n'+'x '*790+'\nResponda somente OK.'
while True:
 ms=[{'role':'user','content':msg}];n=len(tok.encode(render(ms,False),add_special_tokens=False))
 if n>2048:break
 msg='x '+msg
(HERE/'fixtures/context_over2048.json').write_text(json.dumps(ms,ensure_ascii=False)+'\n');(HERE/'fixtures/context_options.json').write_text(json.dumps({'thinking':False,'reasoning_tokens':0,'response_tokens':16,'context_tokens':16384})+'\n')
report={'status':'HF_templates_verified','cases':rows,'actual_native_checks':'toolcheck verifies original3nonthinking fixtures on every native run; thinking arithmetic prompt token count compared separately','python_transcription_of_native_rendering_not_independent_compiled_render_test':True,'expected_arithmetic_prompt_tokens':expected,'long_context_prompt_tokens':n,'no_model_weights_loaded':True}
(HERE/'reports/hf_template_checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
