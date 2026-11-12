"""Cold-load the separately preserved specialist without resetting its text weights."""
import sys,argparse,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from train_runtime import load as load_parent,e,torch,PARENT_HASH
import checkpoint
HERE=Path(__file__).resolve().parent
@torch.inference_mode()
def load_specialist():
    model,tok,_,meta=load_parent()
    manifest=checkpoint.restore(HERE/'checkpoints/final',model,PARENT_HASH)
    meta.update(variant='full_text_supervised_specialist_015_attempt_b',checkpoint_stream_sha256=manifest['stream_sha256'])
    training=json.loads((HERE/'training_complete.json').read_text())
    meta['architecture']=e.cr.check_architecture(model,2)
    meta['architecture'].update(backward_passes=training['backward_passes'],limitations='Qwen widths; trained Loop/mHC and Liquid-inspired operators, not full SenseNova/LFM3.')
    return model,tok,meta

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prompt',required=True);p.add_argument('--max-tokens',type=int,default=320)
    args=p.parse_args();model,tok,meta=load_specialist()
    output=e.cr.generate(model,tok,args.prompt,max_tokens=args.max_tokens);output.pop('trace',None)
    print(json.dumps({'metadata':meta,**output},ensure_ascii=False))
if __name__=='__main__':main()
