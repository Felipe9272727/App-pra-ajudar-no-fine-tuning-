"""Check contiguous local records, not only central-directory names and signature."""
import hashlib,json,struct,sys,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent
def audit(path):
    with zipfile.ZipFile(path) as z:
        infos=sorted(z.infolist(),key=lambda i:i.header_offset);position=0;gaps=[];alignment=[]
        for i in infos:
            if i.header_offset!=position:gaps.append({'before':i.filename,'bytes':i.header_offset-position})
            with path.open('rb') as f:
                f.seek(i.header_offset);head=f.read(30);assert head[:4]==b'PK\x03\x04';nl,el=struct.unpack_from('<HH',head,26);assert f.read(nl).decode()==i.filename
            data=i.header_offset+30+nl+el;position=data+i.compress_size
            if i.flag_bits&8:
                with path.open('rb') as f:f.seek(position);sig=f.read(4)
                position+=16 if sig==b'PK\x07\x08' else 12
            if i.compress_type==0 and data%4:alignment.append(i.filename)
        with path.open('rb') as f:
            f.seek(z.start_dir-24);footer=f.read(24);assert footer[8:]==b'APK Sig Block 42';block_size=struct.unpack('<Q',footer[:8])[0]+8;signing_start=z.start_dir-block_size
        padding=0
        if position!=signing_start:
            gap=signing_start-position
            with path.open('rb') as f:f.seek(position);zero=f.read(gap) if 0<gap<4096 else b'not-padding'
            if 0<gap<4096 and signing_start%4096==0 and not any(zero):padding=gap
            else:gaps.append({'before':'signing block','bytes':gap})
        assert z.getinfo('resources.arsc').compress_type==0
        return {'entries':len(infos),'unreferenced_or_gap_regions':gaps,'misaligned_stored_entries':alignment,'contiguous_local_records':not gaps,'one_trailing_APK_signing_block_after_last_local_record':position+padding==signing_start,'signer_zero_alignment_padding_bytes':padding,'first_local_entry':infos[0].filename}
if __name__=='__main__':
    p=Path(sys.argv[1]);r=audit(p);print(json.dumps(r,indent=2));
    if '--strict'in sys.argv:assert r['contiguous_local_records'] and not r['misaligned_stored_entries'] and r['first_local_entry']=='AndroidManifest.xml'
