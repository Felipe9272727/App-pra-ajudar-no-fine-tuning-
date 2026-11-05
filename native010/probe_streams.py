"""Mechanism diagnostic on unlabelled context; does not select model weights."""
import sys,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,torch,e
from native010.native_runtime import build,verify_bundle

@torch.inference_mode()
def main():
 status=json.loads((HERE/'status.json').read_text());status.update(status='mechanism_probe',model_process_active=True);e.cr.atomic_json(HERE/'status.json',status)
 model,tok,parent,meta=load();build(model,'routed',HERE);verify_bundle(model,'routed',HERE)
 stats={};handles=[]
 for i,l in enumerate(model.model.language_model.layers[4:28],4):
  for name in ['mhc_attn','mhc_ffn']:
   key=f'{i}.{name}';stats[key]={'calls':0,'maximum_stream_difference':0.,'maximum_post_difference':0.,'maximum_row_sum_error':0.,'maximum_col_sum_error':0.}
   def hook(module,inputs,output,key=key):
    x=inputs[0].detach().float();post=output[1];mix=output[2];s=stats[key];s['calls']+=1
    s['maximum_stream_difference']=max(s['maximum_stream_difference'],float((x[...,0,:]-x[...,1,:]).abs().max()))
    s['maximum_post_difference']=max(s['maximum_post_difference'],float((post[...,0]-post[...,1]).abs().max()))
    s['maximum_row_sum_error']=max(s['maximum_row_sum_error'],float((mix.sum(-1)-1).abs().max()))
    s['maximum_col_sum_error']=max(s['maximum_col_sum_error'],float((mix.sum(-2)-1).abs().max()))
   handles.append(getattr(l,name).register_forward_hook(hook))
 text='Uma observação descreve o que foi visto; uma interpretação tenta explicar por que aconteceu.'
 x=tok(text,add_special_tokens=False,return_tensors='pt')['input_ids']
 model(input_ids=x,use_cache=False,logits_to_keep=1)
 for h in handles:h.remove()
 out={'input_is_unlabelled':True,'generated_answers':False,'per_router':stats,
  'routers_with_observed_stream_separation':sum(s['maximum_stream_difference']>0 for s in stats.values()),
  'routers_with_observed_conditional_post_gates':sum(s['maximum_post_difference']>0 for s in stats.values()),
  'maximum_stream_difference':max(s['maximum_stream_difference'] for s in stats.values()),
  'used_to_select_weights':False}
 status.update(status='mechanism_probe_complete',model_process_active=False);e.cr.atomic_json(HERE/'status.json',status)
 e.cr.atomic_json(HERE/'stream_probe.json',out);print(json.dumps({k:v for k,v in out.items() if k!='per_router'}))
if __name__=='__main__':main()
