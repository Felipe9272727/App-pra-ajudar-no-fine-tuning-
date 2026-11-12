"""Export the exact selected hybrid to a checked, deduplicated mobile weight pack."""
import sys,json,hashlib,struct,argparse,math,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,torch,PARENT_HASH
HEADER=1024*1024

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()

@torch.inference_mode()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--modes',nargs='+',default=['bf16','q8']);ap.add_argument('--reference',action='store_true');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 model,tok,parent,meta=load();assert PARENT_HASH=='46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'
 params={n.removeprefix('model.language_model.'):p for n,p in model.named_parameters() if n.startswith('model.language_model.')}
 assert len(params)==546
 streams={};seen={};entries={};stats={}
 for mode in a.modes:
  assert mode in ['bf16','q8'];path=a.out/(mode+'.lsp');assert not path.exists(),'Never overwrite a model export'
  f=path.open('w+b');f.write(bytes(HEADER));streams[mode]=f;seen[mode]={};entries[mode]={};stats[mode]=[]
 for name,p in params.items():
  raw=p.detach().contiguous().view(torch.uint8).numpy().tobytes();source=hashlib.sha256(raw).hexdigest();shape=list(p.shape);iszero=not bool(p.count_nonzero())
  for mode,f in streams.items():
   key=(source,str(p.dtype),tuple(shape));spec={'shape':shape,'source_dtype':str(p.dtype),'source_sha256':source}
   if key in seen[mode]:entries[mode][name]={**seen[mode][key],**spec};continue
   error=0.;maximum=0.
   if iszero:kind='zero';data=b''
   elif mode=='q8' and p.ndim==2 and p.shape[1]%32==0 and '.mhc_' not in '.'+name:
    blocks=p.float().reshape(-1,32);scale=blocks.abs().amax(1).clamp_min(1e-20)/127.;q=(blocks/scale[:,None]).round().clamp(-127,127).to(torch.int8)
    # One f32 scale followed by32 signed bytes, in contiguous row/block order.
    encoded=torch.cat([scale.view(torch.uint8).reshape(-1,4),q.view(torch.uint8)],1).contiguous();data=encoded.numpy().tobytes();kind='q8_32'
    d=q.float()*scale[:,None]-blocks;error=float(d.square().mean().sqrt());maximum=float(d.abs().max());del blocks,scale,q,encoded,d
   elif p.dtype==torch.float32:kind='f32';data=raw
   else:assert p.dtype==torch.bfloat16;kind='bf16';data=raw
   pad=(-f.tell())%64;f.write(bytes(pad));offset=f.tell();f.write(data)
   spec.update(kind=kind,offset=offset,bytes=len(data),data_sha256=hashlib.sha256(data).hexdigest())
   seen[mode][key]=spec;entries[mode][name]=spec;stats[mode].append({'name':name,'kind':kind,'rms_error':error,'max_abs_error':maximum})
  print('EXPORT',name,flush=True)
 manifests={}
 for mode,f in streams.items():
  manifest={'format':'liquid-sense-pack-v1','checkpoint':'general-principal','source_checkpoint_sha256':PARENT_HASH,'quantization':mode,'hidden_size':1024,'vocab_size':248320,'eos_token_id':248044,'text_parameters':sum(p.numel() for p in params.values()),'tensor_count':546,'physical_layers':32,'execution_plan':list(model.model.language_model._loop_plan),'mhc':model.config.mhc,'windows':[7,15,27],'window_size':256,'conv_kernel':7,'tensors':entries[mode],'header_bytes':HEADER,'context_limit':2048,'native_widths':True,'vision_included':False,'vision_omission_reason':'Text-only chat; all text and temporal/loop tensors retained.'}
  payload=json.dumps(manifest,separators=(',',':')).encode();assert len(payload)+16<HEADER;f.seek(0);f.write(b'LSENSE01'+struct.pack('<Q',len(payload))+payload);f.close();path=a.out/(mode+'.lsp')
  report={'manifest':manifest,'bytes':path.stat().st_size,'sha256':digest(path),'quantization_error':stats[mode]};(a.out/(mode+'_export.json')).write_text(json.dumps(report,indent=2)+'\n');manifests[mode]={'bytes':report['bytes'],'sha256':report['sha256']}
 (a.out/'tokenizer.json').write_bytes((ROOT/'upstream/tokenizer.json').read_bytes());info=json.loads((ROOT/'model_identity.json').read_text());(a.out/'identity.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
 messages=[{'role':'system','content':info['system_message']},{'role':'user','content':'Olá!'}];rendered=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False);ids=tok.encode(rendered,add_special_tokens=False)
 (a.out/'tokenizer_fixture.json').write_text(json.dumps({'messages':messages,'rendered':rendered,'ids':ids},ensure_ascii=False,indent=2)+'\n')
 if a.reference:
  cache=None;steps=[]
  for ident in ids[:2]:
   out=model.model.language_model(input_ids=torch.tensor([[ident]]),past_key_values=cache,use_cache=True,output_hidden_states=True);cache=out.past_key_values;logits=model.lm_head(out.last_hidden_state[:,-1]).float()[0];values,indices=logits.topk(32)
   steps.append({'input_id':ident,'states':[s[0,-1].float().tolist() for s in out.hidden_states],'argmax':int(indices[0]),'top_ids':indices.tolist(),'top_logits':values.tolist()})
  (a.out/'python_reference.json').write_text(json.dumps({'precision':'bfloat16','prefill':'sequential one-token cached; compares matching numerical path, not full-prefill benchmark','steps':steps},separators=(',',':'))+'\n')
 print('EXPORT_COMPLETE',json.dumps(manifests),flush=True)
if __name__=='__main__':main()
