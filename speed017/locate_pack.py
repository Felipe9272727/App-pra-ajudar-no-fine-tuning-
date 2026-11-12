"""Locate/verify the exact stored model asset without extracting a duplicate."""
import argparse,zipfile,struct,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('apk',type=Path);p.add_argument('output',type=Path);a=p.parse_args();assert not a.output.exists(),'Do not replace an existing locator silently'
with zipfile.ZipFile(a.apk) as z:
 info=z.getinfo('assets/model.lsp');assert info.compress_type==zipfile.ZIP_STORED
 with a.apk.open('rb') as f:
  f.seek(info.header_offset);head=f.read(30);assert head[:4]==b'PK\x03\x04';nl,ex=struct.unpack_from('<HH',head,26);offset=info.header_offset+30+nl+ex;f.seek(offset);h=hashlib.sha256();left=info.file_size
  while left:
   b=f.read(min(8*1024*1024,left));assert b;h.update(b);left-=len(b)
 assert h.hexdigest()=='6c774a434438add704b1993b8e013493fb95bc9802c4d9b30227832115c07288'
 a.output.write_text(json.dumps({'path':str(a.apk.resolve()),'offset':offset,'length':info.file_size,'sha256':h.hexdigest(),'model_unchanged':True},indent=2)+'\n')
