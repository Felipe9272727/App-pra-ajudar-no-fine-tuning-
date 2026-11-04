"""Replay the saved V3 experiment without repeating its calibration."""
import argparse
import json
from runtime import *
from evaluate import make_experiment


def main():
    p=argparse.ArgumentParser();p.add_argument('--question',required=True)
    a=p.parse_args();f=json.loads((HERE/'frozen.json').read_text())
    for path,key in [(ROOT/f['checkpoint'],'checkpoint_sha256'),(HERE/'codec.pt','codec_sha256'),
                     (HERE/'query_embeddings.pt','query_embeddings_sha256'),(PARENT_PATCH,'parent_patch_sha256')]:
        assert file_hash(path)==f[key],f'Checkpoint changed: {path.name}'
    model,_=parent_model();tok=tokenizer()
    exp=make_experiment(model,tok,ROOT/f['checkpoint'])
    output,trace=exp.generate(a.question)
    print(json.dumps({'model':f['model_name'],'scope':'EXPERIMENTO, up to 8 output bytes',
        'output':output,'trace':trace},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
