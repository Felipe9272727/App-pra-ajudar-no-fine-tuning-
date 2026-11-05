"""Finalize rejected native ablations only; never promotes a checkpoint."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def read(name):return json.loads((HERE/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(name,obj):(HERE/name).write_text(json.dumps(obj,indent=2)+'\n')

def main():
 comparison=read('screen_comparison.json');assert len(comparison['candidates'])==3
 assert not any(x['full_development_eligible'] for x in comparison['candidates'].values()),'An eligible candidate needs full gates, not rejection finalization'
 frozen=read('native_frozen.json')
 assert all(sha(ROOT/p)==h for p,h in frozen['files'].items())
 parent_hash=sha(ROOT/'rsi100/checkpoints/best.pt')
 selection={'selected':'parent','checkpoint':'rsi100/checkpoints/best.pt','checkpoint_sha256':parent_hash,
  'checkpoint_promoted':False,'fresh_validation_consumed':False,
  'reason':'All three native ablations failed the predeclared development screen; preserve unchanged parent',
  'native_candidates_saved':['native010/checkpoint_'+x+'.json' for x in ['depth','liquid','routed']],
  'monolithic_native_safetensors_exported':False,'incremental_reconstruction_bitwise_verified':True}
 put('selection.json',selection)
 for p in Path('/workspace/scratch').glob('native010-*.log'):
  (HERE/'logs'/(p.stem+'.txt')).write_text(p.read_text())
 put('status.json',{'status':'complete_rejected_parent_retained','model_process_active':False,'process_continues_in_background':False,
  'checkpoint_promoted':False,'selected':'parent','parent_sha256':parent_hash,
  'audit_values':read('audit_complete.json')['unique_parameter_values'],'native_ablations_completed':3,
  'native_checkpoint_manifests_saved':True,'technical_tests_passed':55,'backward_passes':0,
  'independent_validation_consumed':False,'source_frozen_integrity_verified':True,'report':'NATIVE_ARCHITECTURE_REPORT.md'})
 all_files=[ROOT/'NATIVE_ARCHITECTURE_REPORT.md',ROOT/'AGENTS.md']+[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix not in ['.pt','.zip'] and p.name!='artifact_integrity.json']
 put('artifact_integrity.json',{'sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(all_files)},
  'binary_checkpoints':{str(p.relative_to(ROOT)):sha(p) for p in (HERE/'checkpoints').glob('*.pt')},
  'row_column_norms_sha256':sha(HERE/'row_column_norms.pt'),'unloaded_row_column_norms_sha256':sha(HERE/'unloaded_row_column_norms.pt'),'parent_unchanged':True})
 print(json.dumps(selection,indent=2))
if __name__=='__main__':main()
