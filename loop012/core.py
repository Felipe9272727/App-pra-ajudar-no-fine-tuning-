"""Shared diagnostic helpers; no gradients, conventional training or gold inputs."""
import json,sys,copy,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'loop012'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,e,torch,PARENT_HASH,tensor_checkpoint,tasks
from native010.native_runtime import tensor_hash
from native_runtime import SOURCE_LAYERS
ERRORS=['prefix_sums','overlap_count','run_lengths','rotate_right','longest_run'];GUARDS=['sum_abs','binary_search'];SCREEN=ERRORS+GUARDS
LAYERS=[6,25];TARGETS=['overlap_count','longest_run']
def save(name,obj):e.cr.atomic_json(HERE/name,obj)
def state(phase,active=False):save('status.json',{'status':phase,'model_process_active':active,'parent_sha256':PARENT_HASH,'checkpoint_promoted':False,'backward_passes':0,'fresh_validation_consumed':False})
def verify():
 for path,h in json.loads((HERE/'frozen.json').read_text())['files'].items():assert e.cr.file_hash(ROOT/path)==h,path

def original_rows():return json.loads((ROOT/'reasoning/cycle2/development_original.json').read_text())['rows']
def parent_rows():return json.loads((ROOT/'reasoning/cycle2/trial_006_parent_full.json').read_text())['rows']

def load_variant(kind):
 if kind=='original':m,meta=e.cr.load('original');return m,e.cr.tokenizer(),meta
 m,t,p,meta=load()
 if kind in ['target','inverse']:
  patch=torch.load(HERE/'checkpoints'/f'{kind}.pt',weights_only=True)
  for i,w in patch['weights'].items():
   param=m.model.language_model.layers[int(i)].linear_attn.in_proj_a.weight
   assert tensor_hash(param)==patch['parent_tensor_hashes'][i];param.copy_(w)
   assert tensor_hash(param)==patch['written_tensor_hashes'][i]
  meta['gate_patch_sha256']=e.cr.file_hash(HERE/'checkpoints'/f'{kind}.pt')
 return m,t,meta

class BypassSecond:
 def __init__(self,model):self.first=None;self.layer=model.model.language_model.layers[27];self.handle=None;self.calls=0
 def hook(self,module,args,output):
  visit=module._last_native_visit
  if visit==0:self.first=output.detach().clone()
  else:
   assert visit==1 and self.first.shape==output.shape;self.calls+=1
   return self.first.clone()
 def __enter__(self):self.handle=self.layer.register_forward_hook(self.hook);return self
 def __exit__(self,*args):self.handle.remove()


def style_metrics(text,task):
 import json,re
 sentences=[s for s in re.split(r'[.!?]+(?=\s|$)',text.strip()) if s.strip()]
 bullets=re.findall(r'^\s*(?:[-*•]|\d+[.)])\s+',text,re.M)
 words=re.findall(r'\b\w+\b',text.lower());grams=list(zip(words,words[1:],words[2:]));repeat=1-len(set(grams))/len(grams) if grams else 0.
 passed=None;detail={}
 if task in ['explain_cache_pt','explain_test_en']:passed=len(sentences)==2 and not bullets
 elif task=='polite_rewrite_pt':passed=bool(text.strip()) and not bullets and not re.match(r'^(claro|aqui|here|sure)\b',text.strip(),re.I)
 elif task=='uncertainty_pt':passed=len(bullets)==3
 elif task=='summary_pt':passed=len(sentences)==1
 elif task=='structured_pt':
  try:
   v=json.loads(text);passed=isinstance(v,dict) and set(v)=={'nome','quantidade','disponivel'} and str(v['nome']).casefold()=='caderno' and type(v['quantidade']) is int and v['quantidade']==3 and v['disponivel'] is True
  except (ValueError,KeyError,TypeError):passed=False
 return {'words':len(words),'characters':len(text),'sentences_heuristic':len(sentences),'bullet_lines':len(bullets),'repeated_word_trigram_fraction':repeat,'structural_instruction_pass':bool(passed)}
