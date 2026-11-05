"""Finalize the rejected finite study and immutable artifact inventory."""
from pathlib import Path
import json,hashlib,importlib.metadata,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(n):return json.loads((HERE/n).read_text())
def write(n,obj):(HERE/n).write_text(json.dumps(obj,indent=2)+'\n')
def main():
 decision=read('decision.json');assert not decision['eligible_full']
 for path,digest in read('frozen.json')['files'].items():assert sha(ROOT/path)==digest,path
 parent='46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8';assert sha(ROOT/'rsi100/checkpoints/best.pt')==parent
 for kind in ['target','inverse']:assert sha(HERE/'checkpoints'/f'{kind}.pt')==read('technical.json')['variants'][kind]['checkpoint_sha256']
 assert read('recovery.json')['paired_parent_replay_matches_all_old_outputs_and_case_bits']
 for p in Path('/workspace/scratch').glob('loop012-*.log'):(HERE/'logs'/(p.stem+'.txt')).write_text(p.read_text())
 for p in (HERE/'logs').glob('*.txt'):p.write_text(p.read_text())
 write('runtime.json',{'python':sys.version.split()[0],'packages':{p:importlib.metadata.version(p) for p in ['torch','transformers','numpy','safetensors','accelerate']},'inference_threads':4,'gpu_used':False,'environment_restarted_and_paired_reference_rechecked':True})
 write('selection.json',{'selected':'parent','checkpoint':'rsi100/checkpoints/best.pt','checkpoint_sha256':parent,'checkpoint_promoted':False,'fresh_validation_consumed':False,
  'reason':'Protected temporal gate edit and inverse tied parent with zero complete-task gain','experimental_overlays':['loop012/checkpoints/target.pt','loop012/checkpoints/inverse.pt']})
 write('status.json',{'status':'complete_rejected_parent_retained','model_process_active':False,'process_continues_in_background':False,'checkpoint_promoted':False,'parent_sha256':parent,
  'new_weight_edits_tested':1,'matched_inverse_controls':1,'changed_values_target':24522,'changed_tensors_target':2,'new_technical_tests_passed':5,
  'backward_passes':0,'independent_validation_consumed':False,'loop_influence_measured':True,'loop_coding_benefit_established':False,
  'language_pairs':6,'language_general_superiority_established':False,'report':'LOOP_LANGUAGE_RESEARCH_REPORT.md'})
 paths=[ROOT/'AGENTS.md',ROOT/'LOOP_LANGUAGE_RESEARCH_REPORT.md',ROOT/'tests/test_loop_specialization.py']+[p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name!='artifact_integrity.json']
 write('artifact_integrity.json',{'sha256':{str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)},'parent_unchanged':True,'frozen_sources_verified':True})
 print('Finite study complete; rejected overlays preserved; parent unchanged.')
if __name__=='__main__':main()
