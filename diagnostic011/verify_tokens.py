"""Verify greedy token capture against actual next-frame embedding inputs."""
from pathlib import Path
import json
import torch
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'diagnostic011'

def main():
 torch.set_num_threads(1)
 eos=json.loads((ROOT/'upstream/config.json').read_text())['text_config']['eos_token_id'];assert isinstance(eos,int)
 rows=[]
 for path in sorted((HERE/'activations').glob('*.pt')):
  p=torch.load(path,weights_only=True);j=next(i for i,(n,v) in enumerate(p['slots']) if n.endswith('.embed_tokens'))
  # These statistics are the exact scalar integer token ID, converted to FP32;
  # all vocabulary IDs are exactly representable, not a lossy average.
  actual=p['per_frame_module_statistics'][1:,j,1].long();recorded=p['own_generated_token_ids']
  assert torch.equal(actual,recorded[:-1]),path.name
  assert len(recorded)<p['protocol']['max_new_tokens'] and int(recorded[-1])==eos,path.name
  rows.append({'id':path.stem,'tokens':len(recorded),'all_nonterminal_ids_verified_against_actual_embedding_inputs':True,
    'terminal_id_verified_as_unique_configured_eos':eos,'suspected_point_snapshot_captured':p['suspected_point']['actual_suspected_point_snapshot_present']})
 assert len(rows)==7
 report={'status':'complete','total_tokens':sum(r['tokens'] for r in rows),'all_actual_ids_verified':True,'rows':rows}
 (HERE/'token_integrity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
