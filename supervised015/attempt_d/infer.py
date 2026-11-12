"""Unforced native inference from the exact final readout specialist."""
import json,argparse
from pathlib import Path
from restore import load_d,e
HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prompt',required=True);p.add_argument('--max-tokens',type=int,default=320);args=p.parse_args()
    model,tok,meta,manifest=load_d();meta.update(variant='cached_readout_specialist_015d',checkpoint_stream_sha256=manifest['stream_sha256'],forced_tokens=False)
    training=json.loads((HERE/'training_complete.json').read_text());meta['architecture']=e.cr.check_architecture(model,2)
    meta['architecture'].update(backward_passes=training['new_total_gradient_updates_in_lineage'],limitations='Trained hybrid; specialization is not general superiority.')
    meta['native_eos_token_id']=model.generation_config.eos_token_id
    result=e.cr.generate(model,tok,args.prompt,max_tokens=args.max_tokens);result.pop('trace',None)
    print(json.dumps({'metadata':meta,**result},ensure_ascii=False))
if __name__=='__main__':main()
