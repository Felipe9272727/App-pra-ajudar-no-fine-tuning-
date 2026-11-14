"""Seek the preserved exact base pack without materializing another 1.6GB copy."""
import bisect, hashlib, json, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'tooluse022/apk_archive'
class PackSource:
    def __init__(self):
        self.archive=json.loads((ARCHIVE/'manifest.json').read_text())
        self.parts=self.archive['pack']['parts'];self.starts=[];n=0
        for part in self.parts:self.starts.append(n);n+=part['bytes']
        self.size=n
        header=self.read(0,1024*1024)
        assert header[:8]==b'LSENSE01'
        self.manifest=json.loads(header[16:16+int.from_bytes(header[8:16],'little')])
    def read(self,offset,length):
        assert 0<=offset<=offset+length<=self.size
        result=bytearray()
        while length:
            i=bisect.bisect_right(self.starts,offset)-1;p=self.parts[i]
            inner=offset-self.starts[i];take=min(length,p['bytes']-inner)
            if 'source' in p:
                with (ROOT/p['source']).open('rb') as f:f.seek(p['offset']+inner);block=f.read(take)
            else:
                raw=zlib.decompress((ARCHIVE/p['compressed']).read_bytes())
                assert len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256']
                block=raw[inner:inner+take]
            assert len(block)==take;result.extend(block);offset+=take;length-=take
        return bytes(result)
