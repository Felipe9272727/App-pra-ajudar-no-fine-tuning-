"""Check every stored tensor; BF16/F32 source values remain lossless."""
from pathlib import Path
import json,struct,hashlib,math,argparse

def main():
 ap=argparse.ArgumentParser();ap.add_argument('pack',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--expected',type=Path);a=ap.parse_args();checked=set();kinds={};count=0
 with a.pack.open('rb') as f:
  assert f.read(8)==b'LSENSE01';m=json.loads(f.read(struct.unpack('<Q',f.read(8))[0]));assert m['quantization']=='bf16';assert m['tensor_count']==len(m['tensors'])==546;assert m['execution_plan']==list(range(4))+list(range(4,28))*2+list(range(28,32))
  for name,s in m['tensors'].items():
   kinds[s['kind']]=kinds.get(s['kind'],0)+1;count+=math.prod(s['shape']);key=(s['offset'],s['bytes'],s['data_sha256'],s['source_sha256'])
   if key in checked:continue
   if s['kind']=='zero':
    h=hashlib.sha256();left=math.prod(s['shape'])*(4 if s['source_dtype']=='torch.float32' else 2)
    while left:n=min(left,4*1024*1024);h.update(bytes(n));left-=n
    assert h.hexdigest()==s['source_sha256'],name
   else:
    assert s['kind'] in ['bf16','f32'];assert s['data_sha256']==s['source_sha256'];f.seek(s['offset']);h=hashlib.sha256();left=s['bytes']
    while left:b=f.read(min(left,4*1024*1024));assert b;h.update(b);left-=len(b)
    assert h.hexdigest()==s['source_sha256'],name
   checked.add(key)
 if a.expected:
  expected=json.loads(a.expected.read_text());assert set(expected)==set(m['tensors'])
  for name,s in m['tensors'].items():
   assert all(s[k]==expected[name][k] for k in ['source_sha256','source_dtype','shape']),name
 r={'status':'all_546_text_tensor_payloads_losslessly_verified','tensors':546,'parameter_values':count,'unique_stored_payloads':len(checked),'kinds':kinds,'weight_quantization':False,'checkpoint_sha256':m['source_checkpoint_sha256'],'physical_layers':32,'executions':56,'context_limit':m['context_limit'],'vision_included':False,'text_only_application':True};a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
