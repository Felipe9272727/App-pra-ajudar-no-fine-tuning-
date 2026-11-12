"""Cold restore exact015E then the checked016 XOR; never reset learned loop gains."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'supervised015'))
from supervised015.attempt_e.restore import load_d as load_e
from supervised015 import checkpoint
E_HASH='33f4d2b0fa0d36329ec0bd59d94ca9054c5c4ab549b7a551743a955711679b85'
def load_candidate():
    model,tok,meta,parent=load_e();assert parent['stream_sha256']==E_HASH
    manifest=checkpoint.restore(ROOT/'balanced016/checkpoints/final',model,E_HASH)
    return model,tok,meta,manifest
