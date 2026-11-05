"""Always reload a cold parent, then verify and reconstruct a native experiment.

These candidates are experimental. This does not replace the selected best.pt.
Native bundles use this loader; legacy load_port alone resets their changes.
"""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'reasoning'))
from runtime_helpers import load,e,torch,PARENT_HASH
from native010.native_runtime import build,verify_bundle,modified_parameters,tensor_hash

@torch.inference_mode()
def load_candidate(variant):
 assert variant in ['depth','liquid','routed']
 manifest=json.loads((HERE/f'checkpoint_{variant}.json').read_text())
 assert manifest['parent_sha256']==PARENT_HASH
 assert e.cr.file_hash(HERE/'native_frozen.json')==manifest['source_manifest_sha256']
 frozen=json.loads((HERE/'native_frozen.json').read_text())
 for path,digest in frozen['files'].items():assert e.cr.file_hash(ROOT/path)==digest,path
 for name,digest in manifest['overlay_sha256'].items():assert e.cr.file_hash(HERE/'checkpoints'/name)==digest,name
 model,tok,parent,meta=load()
 audit={r['name']:r['sha256_values'] for r in map(json.loads,(HERE/'parameters.jsonl').read_text().splitlines())}
 complete_parent={n:tensor_hash(p) for n,p in model.named_parameters()}
 assert complete_parent==audit,'Full selected-parent parameter mismatch'
 actual={n:tensor_hash(p) for n,p in modified_parameters(model,variant).items()}
 assert actual==manifest['parent_tensor_hashes'],'Loaded model is not the frozen parent'
 arch=build(model,variant,HERE);verify_bundle(model,variant,HERE)
 meta.update(experimental_native_variant=variant,architecture=arch,checkpoint_promoted=False,
  incremental_manifest_sha256=e.cr.file_hash(HERE/f'checkpoint_{variant}.json'))
 return model,tok,meta

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('variant',choices=['depth','liquid','routed']);p.add_argument('--prompt');p.add_argument('--max-new-tokens',type=int,default=160);a=p.parse_args()
 model,tok,meta=load_candidate(a.variant)
 if a.prompt is None:print(json.dumps(meta,indent=2))
 else:print(e.cr.generate(model,tok,a.prompt,max_tokens=a.max_new_tokens)['output'])
