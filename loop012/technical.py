"""Cold reconstruction, exactly-two-tensor edit and cache checks."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from loop012.core import *
@torch.inference_mode()
def main():
 verify();reference={r['name']:r['sha256_values'] for r in map(json.loads,(ROOT/'native010/parameters.jsonl').read_text().splitlines())}
 reports={}
 for kind in ['target','inverse']:
  m,t,meta=load_variant(kind);actual={n:tensor_hash(p) for n,p in m.named_parameters()}
  changed=[n for n in actual if actual[n]!=reference[n]];assert set(changed)=={f'model.language_model.layers.{i}.linear_attn.in_proj_a.weight' for i in LAYERS}
  arch=e.cr.check_architecture(m,2);cache=e.cr.cache_check(m,t,2)
  reports[kind]={'exactly_changed_tensors':changed,'architecture':arch,'cache':cache,'checkpoint_sha256':e.cr.file_hash(HERE/'checkpoints'/f'{kind}.pt')}
  del m
 save('technical.json',{'status':'complete','variants':reports});print('COLD_TECHNICAL_CHECKS_COMPLETE',flush=True)
if __name__=='__main__':main()
