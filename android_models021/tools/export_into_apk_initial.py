"""Lossless exact015E export directly to the aligned unsigned APK (no duplicate pack)."""
import sys,json,hashlib,struct,zipfile,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
from supervised015.attempt_e.restore import load_d
from train_runtime import torch,e,tensor_hash
HERE=ROOT/'android_models021';HEADER=1024*1024;CHUNK=4*1024*1024

def save(n,x):e.cr.atomic_json(HERE/'reports'/n,x)
def chunks(p):yield from p.detach().contiguous().view(torch.uint8).flatten().split(CHUNK)
def aligned_info(z,name,size):
 info=zipfile.ZipInfo(name,date_time=(2026,11,12,0,0,0));info.compress_type=zipfile.ZIP_STORED;info.file_size=size
 start=z.fp.tell()+30+len(name.encode('utf-8'))
 if start%4:
  pad=(-(start+4))%4;info.extra=struct.pack('<HH',0xFFFF,pad)+bytes(pad)
 return info
@torch.inference_mode()
def main():
 apk=Path(sys.argv[1]);assert apk.exists();assert not (HERE/'reports/specialist_export.json').exists(),'Inspect completed export instead of rerunning'
 started=time.monotonic();expected=json.loads((HERE/'expected_specialist.json').read_text());model,tok,meta,last=load_d();assert last['stream_sha256']==expected['E_stream'];assert model.generation_config.eos_token_id==248044
 params={n:p for n,p in model.named_parameters() if n.startswith('model.language_model.')};assert len(params)==546
 with zipfile.ZipFile('/dev/shm/liquid-android/apk/LiquidSense-0.1.0-preview.apk') as old:
  with old.open('assets/model.lsp') as f:assert f.read(8)==b'LSENSE01';length=struct.unpack('<Q',f.read(8))[0];manifest=json.loads(f.read(length))
 specs={};seen={};sources={};cursor=HEADER;raw_total=0
 for full,p in params.items():
  sha=hashlib.sha256();zero=True
  for block in chunks(p):
   b=block.numpy().tobytes();sha.update(b)
   if zero and any(b):zero=False
  h=sha.hexdigest();ref=expected['text_tensors'][full];assert list(p.shape)==ref['shape'] and str(p.dtype)==ref['dtype'] and h==ref['sha256'],full
  name=full.removeprefix('model.language_model.');kind='zero' if zero else 'f32' if p.dtype==torch.float32 else 'bf16';assert p.dtype in (torch.bfloat16,torch.float32);key=(h,str(p.dtype),tuple(p.shape));raw_total+=p.numel()*p.element_size()
  if key in seen:specs[name]={**seen[key]};continue
  cursor+=(-cursor)%64;size=0 if zero else p.numel()*p.element_size();spec={'shape':list(p.shape),'source_dtype':str(p.dtype),'source_sha256':h,'kind':kind,'offset':cursor,'bytes':size,'data_sha256':hashlib.sha256(b'').hexdigest() if zero else h};specs[name]=spec;seen[key]=spec;sources[name]=p;cursor+=size
  print('EXACT_TENSOR',name,flush=True)
 assert sum(p.numel() for p in params.values())==919659696
 manifest.update(checkpoint='specialist015E',source_checkpoint_sha256=expected['E_stream'],source_checkpoint_reference_type='015E_incremental_manifest_stream_not_monolithic_file',source_parent_sha256='46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8',model_fingerprint_sha256=expected['model_fingerprint_sha256'],tensors=specs,quantization='bf16')
 payload=json.dumps(manifest,separators=(',',':')).encode();assert len(payload)+16<HEADER
 # Separate inference-only fixtures; solutions/tests NEVER go into native inputs/APK.
 fixtures=[]
 for role,path,budget in [('taught',ROOT/'supervised015/attempt_e/train.json',320),('controls',ROOT/'review013/controls.json',64)]:
  for row in json.loads(path.read_text()):
   question=row['prompt'] if role=='taught' else row['question'];ids=tok.apply_chat_template([{'role':'user','content':question}],tokenize=True,add_generation_prompt=True,enable_thinking=False)
   rendered='<|im_start|>user\n'+question+'<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n';assert tok.encode(rendered,add_special_tokens=False)==ids
   fixtures.append({'id':row['id'],'role':role,'input_ids':ids,'budget':budget})
 save('native_inputs.json',fixtures)
 free=os.statvfs('/dev/shm');available=free.f_bavail*free.f_frsize;assert available>cursor+8*1024*1024,(available,cursor)
 save('export_preflight.json',{'all546source_hashes_match_C_plus_E':True,'model_fingerprint':expected['model_fingerprint_sha256'],'planned_pack_bytes':cursor,'unique_payloads':len(sources),'free_shm_before_write':available,'no_quantization':True,'native_input_template_matches_all20_HF_prefixes':True,'new_training_updates':0})
 pack_hash=hashlib.sha256();position=0
 with zipfile.ZipFile(apk,'a',allowZip64=False) as z:
  info=aligned_info(z,'assets/model.lsp',cursor);offset=z.fp.tell()+30+len(info.filename.encode())+len(info.extra)
  with z.open(info,'w') as dest:
   def write(b):
    nonlocal position;dest.write(b);pack_hash.update(b);position+=len(b)
   head=b'LSENSE01'+struct.pack('<Q',len(payload))+payload;write(head);write(bytes(HEADER-len(head)))
   for name,p in sources.items():
    spec=specs[name];assert position<=spec['offset'];write(bytes(spec['offset']-position));sha=hashlib.sha256()
    if spec['kind']!='zero':
     for block in chunks(p):b=block.numpy().tobytes();write(b);sha.update(b)
    assert sha.hexdigest()==spec['data_sha256'];print('WRITE',name,flush=True)
   assert position==cursor
 report={'status':'lossless_specialist_export_complete','source_checkpoint':'015E exact B+C+E','E_stream':expected['E_stream'],'model_fingerprint_sha256':expected['model_fingerprint_sha256'],'pack_sha256':pack_hash.hexdigest(),'pack_bytes':cursor,'text_tensors_verified':546,'text_parameters':919659696,'unique_payloads':len(sources),'all_source_and_written_payload_hashes_verified':True,'quantized':False,'new_gradient_updates':0,'physical_layers':32,'executions':56,'mhc_streams':2,'native_source_template':'user-only, nonthinking, trueEOS248044','seconds':time.monotonic()-started}
 save('specialist_export.json',report);save('model_locator.json',{'path':str(apk),'offset':offset,'length':cursor,'sha256':pack_hash.hexdigest()});print('SPECIALIST_EXPORT_DONE',json.dumps(report),flush=True)
if __name__=='__main__':main()
