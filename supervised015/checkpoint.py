"""Exact, streamed XOR checkpoints against the immutable selected parent.

No second monolithic 1.84GB text file is required. Only bytewise differences
are compressed; restoring reconstructs the exact BF16/FP32 values, losslessly.
"""
import gzip,hashlib,io,json,tarfile
from pathlib import Path
import torch
HERE=Path(__file__).resolve().parent
CHUNK=4*1024*1024

class PartsWriter:
    def __init__(self,directory):
        self.directory=directory;directory.mkdir(parents=True,exist_ok=True)
        self.file=None;self.bytes=0;self.parts=[];self.hash=hashlib.sha256();self.part_hash=None
    def write(self,data):
        data=memoryview(data);self.hash.update(data);total=len(data)
        while data:
            if self.file is None:
                path=self.directory/('part%04d.bin'%len(self.parts));self.file=path.open('wb');self.bytes=0;self.part_hash=hashlib.sha256()
            n=min(len(data),CHUNK-self.bytes);piece=data[:n];self.file.write(piece);self.part_hash.update(piece);self.bytes+=n;data=data[n:]
            if self.bytes==CHUNK:self.finish_part()
        return total
    def finish_part(self):
        if self.file is None:return
        name=Path(self.file.name).name;self.file.close();self.parts.append({'path':name,'bytes':self.bytes,'sha256':self.part_hash.hexdigest()});self.file=None
    def flush(self):
        if self.file:self.file.flush()
    def close(self):self.finish_part()

class XorSource:
    def __init__(self,old,new):
        self.old=old.detach().contiguous().view(torch.uint8).flatten();self.new=new.detach().contiguous().view(torch.uint8).flatten()
        integers=torch.int16 if old.element_size()==2 else torch.int32
        self.old_values=old.detach().view(integers).flatten();self.new_values=new.detach().view(integers).flatten()
        self.element=old.element_size();self.pos=0;self.before=hashlib.sha256();self.after=hashlib.sha256();self.changed=0
    def read(self,n):
        n=min(n,len(self.old)-self.pos);a=self.old[self.pos:self.pos+n];b=self.new[self.pos:self.pos+n]
        self.before.update(a.numpy().tobytes());self.after.update(b.numpy().tobytes())
        start=self.pos//self.element;count=n//self.element
        self.changed+=int((self.old_values[start:start+count]!=self.new_values[start:start+count]).count_nonzero())
        self.pos+=n;return torch.bitwise_xor(a,b).numpy().tobytes()

@torch.no_grad()
def write(directory,model,parent,parent_sha256):
    directory=Path(directory);assert not (directory/'manifest.json').exists(),'Never overwrite a checkpoint'
    old=dict(parent.named_parameters());manifest={'format':'gzip-tar-xor-v1','parent_sha256':parent_sha256,'tensors':{},'parts':[]}
    writer=PartsWriter(directory)
    with gzip.GzipFile(fileobj=writer,mode='wb',compresslevel=6,mtime=0) as compressed:
        with tarfile.open(fileobj=compressed,mode='w|',bufsize=CHUNK,copybufsize=CHUNK) as archive:
            for name,p in model.named_parameters():
                if not name.startswith('model.language_model.'):continue
                base=old[name];assert p.shape==base.shape and p.dtype==base.dtype
                reader=XorSource(base,p);info=tarfile.TarInfo(name+'.xor');info.size=p.numel()*p.element_size();info.mtime=0
                archive.addfile(info,reader)
                manifest['tensors'][name]={'shape':list(p.shape),'dtype':str(p.dtype),'bytes':info.size,
                    'parent_tensor_sha256':reader.before.hexdigest(),'tensor_sha256':reader.after.hexdigest(),'changed_values':reader.changed}
    writer.close();manifest['parts']=writer.parts;manifest['stream_sha256']=writer.hash.hexdigest()
    manifest['compressed_bytes']=sum(p['bytes'] for p in writer.parts)
    manifest['changed_tensors']=sum(t['changed_values']>0 for t in manifest['tensors'].values())
    manifest['changed_values']=sum(t['changed_values'] for t in manifest['tensors'].values())
    tmp=directory/'manifest.json.tmp';tmp.write_text(json.dumps(manifest,indent=2)+'\n');tmp.replace(directory/'manifest.json')
    return manifest

class PartsReader:
    def __init__(self,directory,manifest):
        self.directory=directory;self.manifest=manifest;self.index=0;self.file=None;self.hash=hashlib.sha256();self.part_hash=None
    def read(self,n=-1):
        if n<0:n=CHUNK
        out=[];left=n
        while left and self.index<len(self.manifest['parts']):
            part=self.manifest['parts'][self.index]
            if self.file is None:self.file=(self.directory/part['path']).open('rb');self.part_hash=hashlib.sha256()
            b=self.file.read(left)
            if not b:
                assert self.part_hash.hexdigest()==part['sha256'];self.file.close();self.file=None;self.index+=1;continue
            self.part_hash.update(b);self.hash.update(b);out.append(b);left-=len(b)
        return b''.join(out)
    def close(self):
        if self.file:self.file.close();self.file=None
    def __del__(self):self.close()

@torch.inference_mode()
def restore(directory,model,parent_sha256):
    directory=Path(directory);m=json.loads((directory/'manifest.json').read_text());assert m['parent_sha256']==parent_sha256
    params=dict(model.named_parameters());seen=set();reader=PartsReader(directory,m)
    with gzip.GzipFile(fileobj=reader,mode='rb') as compressed:
        with tarfile.open(fileobj=compressed,mode='r|',bufsize=CHUNK) as archive:
            for member in archive:
                assert member.isfile() and member.name.endswith('.xor')
                name=member.name[:-4];assert name in m['tensors'] and name not in seen;seen.add(name)
                p=params[name];spec=m['tensors'][name];assert list(p.shape)==spec['shape'] and str(p.dtype)==spec['dtype']
                dest=p.detach().view(torch.uint8).flatten();assert member.size==len(dest)==spec['bytes']
                source=archive.extractfile(member);before=hashlib.sha256();after=hashlib.sha256();pos=0
                while pos<len(dest):
                    b=source.read(min(CHUNK,len(dest)-pos));assert b
                    block=dest[pos:pos+len(b)];before.update(block.numpy().tobytes())
                    delta=torch.frombuffer(bytearray(b),dtype=torch.uint8);block.bitwise_xor_(delta);after.update(block.numpy().tobytes());pos+=len(b)
                assert before.hexdigest()==spec['parent_tensor_sha256'],name
                assert after.hexdigest()==spec['tensor_sha256'],name
        while compressed.read(CHUNK):pass
    # Drain to verify the final compressed part hash as well.
    while reader.read(CHUNK):pass
    assert seen==set(m['tensors']) and reader.hash.hexdigest()==m['stream_sha256']
    return m
