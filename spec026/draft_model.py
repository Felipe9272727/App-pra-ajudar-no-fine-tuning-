"""Fresh text-only instances of the same native Loop/mHC/GDN family; no weights copied."""
import copy,gc,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import torch
from torch import nn
from torch.nn import functional as F
from transformers.models.qwen3_5 import modeling_qwen3_5 as hf
from modeling_sensenova_loop import SenseNovaLoopConfig,_configure_text_model
from v2_adaptation.native_runtime import NativeTextModel,VisitGatedMHC
import v2_adaptation.native_runtime as native_visit
H=ROOT/'spec026'

def tensor_hash(x):return hashlib.sha256(x.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
def full_config(size):
 d=json.loads((ROOT/'sensenova_port/config.json').read_text());t=d['text_config'];small=size=='small';h=64 if small else 256
 t.update(hidden_size=h,intermediate_size=h*4,num_attention_heads=1 if small else 4,num_key_value_heads=1,head_dim=64,linear_num_key_heads=1 if small else 4,linear_num_value_heads=1 if small else 4,linear_key_head_dim=16 if small else 32,linear_value_head_dim=16 if small else 32,linear_conv_kernel_dim=7,vocab_size=248320,use_cache=True,torch_dtype='float32',dtype='float32')
 t['rope_parameters']=dict(t['rope_parameters'],mrope_section=[3,3,2],partial_rotary_factor=.25)
 d['loop_settings'].update(start=4,end=28,eval_count=2,counts=[2]);d['vision_config']['out_hidden_size']=h;return SenseNovaLoopConfig.from_dict(d)
class TextContainer(nn.Module):
 def __init__(self,config):
  super().__init__();config.text_config._attn_implementation='eager';self.language_model=hf.Qwen3_5TextModel(config.text_config);_configure_text_model(self.language_model,config);self.language_model.__class__=NativeTextModel
  for i in range(4,28):
   l=self.language_model.layers[i];l.__class__=VisitGatedMHC;l.native_visit_gain=nn.Parameter(torch.tensor([.5,.5],dtype=torch.float32));l._native_window=256 if i in [7,15,27] else 0
 def forward(self,**kwargs):return self.language_model(**kwargs)
class DraftLM(nn.Module):
 def __init__(self,size,seed):
  super().__init__();torch.manual_seed(seed);self.config=full_config(size);self.model=TextContainer(self.config);self.size=size;self.seed=seed
 def get_input_embeddings(self):return self.model.language_model.embed_tokens
 def get_output_embeddings(self):return self.model.language_model.embed_tokens
 def hidden(self,ids,cache=None,use_cache=False):return self.model(input_ids=ids,past_key_values=cache,use_cache=use_cache)
 def logits(self,h):return F.linear(h,self.get_input_embeddings().weight)
 def inference_bf16(self):
  saved=[l.native_visit_gain.detach().float().clone() for l in self.model.language_model.layers[4:28]]
  self.to(dtype=torch.bfloat16)
  for l,g in zip(self.model.language_model.layers[4:28],saved):l.native_visit_gain.data=g
  self.eval();self.requires_grad_(False);return self
 def audit(self):
  ps=dict(self.named_parameters());t=self.model.language_model;g=[l.native_visit_gain.detach().tolist() for l in t.layers[4:28]]
  return {'size':self.size,'seed':self.seed,'unique_parameters':sum(p.numel() for p in ps.values()),'tied_embedding_readout':True,'embedding_values':self.get_input_embeddings().weight.numel(),'physical_layers':len(t.layers),'visits':len(t._loop_plan),'virtual_plan':list(t._loop_plan),'mhc_streams':self.config.mhc['streams'],'conv7_layers':sum(l.linear_attn.conv1d.weight.shape[-1]==7 for l in t.layers if hasattr(l,'linear_attn')),'visit_gains':g,'all_finite':all(bool(torch.isfinite(p).all()) for p in ps.values()),'pretrained_weights_loaded':False,'vision_parameters':0}
if __name__=='__main__':
 torch.set_num_threads(4)
 for size in ['small','large']:
  m=DraftLM(size,20261113);a=m.audit();print(json.dumps(a));del m;gc.collect()
