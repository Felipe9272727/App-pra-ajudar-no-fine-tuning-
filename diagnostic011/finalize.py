"""Finalize read-only diagnostics after all observations and archives exist."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(name):return json.loads((HERE/name).read_text())
def write(name,obj):(HERE/name).write_text(json.dumps(obj,indent=2)+'\n')
def main():
 for p in [HERE/'frozen.json',HERE/'gate_probe_frozen.json']:
  for name,digest in json.loads(p.read_text())['files'].items():assert sha(ROOT/name)==digest,name
 capture=read('capture_complete.json');gate=read('gate_probe.json');token=read('token_integrity.json');archive=read('activation_archive.json')
 assert capture['status']==gate['status']==token['status']=='complete'
 assert capture['all_699_parameter_hashes_unchanged'] and gate['all_parameter_hashes_unchanged']
 for member in archive['members']:assert sha(HERE/member['path'])==member['sha256']
 assert sha(HERE/'activation_archive.tar.xz')==archive['archive_sha256']
 for row in archive['chunks']:assert sha(ROOT/row['path'])==row['sha256']
 for row in capture['rows']:assert sha(HERE/'activations'/f"{row['id']}.pt")==row['activations_sha256']
 parent='46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8'
 assert sha(ROOT/'rsi100/checkpoints/best.pt')==parent
 assert read('metric_current.json')['delta_pp'] is None
 for p in Path('/workspace/scratch').glob('diagnostic011-*.log'):(HERE/'logs'/(p.stem+'.txt')).write_text(p.read_text())
 write('selection.json',{'selected':'parent','checkpoint':'rsi100/checkpoints/best.pt','checkpoint_sha256':parent,'checkpoint_promoted':False,
  'new_weight_candidate':False,'reason':'Read-only metric and causal/observational diagnostics; no model-quality gain established','fresh_validation_consumed':False})
 write('status.json',{'status':'complete_analysis_no_weights_changed','model_process_active':False,'process_continues_in_background':False,
  'parent_sha256':parent,'weights_changed':False,'checkpoint_promoted':False,'backward_passes':0,
  'parameter_tensors_catalogued':699,'parameter_tensors_accessed_in_both_groups':546,'actual_decisions':417,'call_slots_per_decision':813,
  'activation_only_probes':30,'probe_argmax_changes':0,'superiority_4b_measured':False,'independent_validation_consumed':False,
  'new_technical_tests_passed':9,'report':'TENSOR_ERROR_ANALYSIS_REPORT.md','raw_tensor_archive_losslessly_verified':True})
 paths=[ROOT/'AGENTS.md',ROOT/'TENSOR_ERROR_ANALYSIS_REPORT.md',ROOT/'tests/test_error_tensor_trace.py']+[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix!='.pt' and not p.name.endswith('.tar.xz') and p.name!='artifact_integrity.json']
 write('artifact_integrity.json',{'sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},'parent_sha256':parent,
  'raw_tensor_members':archive['members'],'all_frozen_sources_verified':True,'raw_tensor_restore_verified':True})
 print('Read-only diagnostics complete; parent preserved.')
if __name__=='__main__':main()
