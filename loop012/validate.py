"""Conditional full gates and unopened independent validation, no tuning."""
import sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from loop012.core import *
from policy import flatten

def dominates_tasks(new,old):
 a=flatten(new['rows']);b=flatten(old['rows']);assert set(a)==set(b)
 return all(not b[k] or a[k] for k in b) and sum(r['all_passed'] for r in new['rows'])>sum(r['all_passed'] for r in old['rows'])
def retained_controls(new,old):return all(not a['correct'] or b['correct'] for a,b in zip(old['controls'],new['controls'])) and len(new['controls'])==len(old['controls'])

def full_decide():
 old=json.loads((ROOT/'reasoning/cycle2/trial_006_parent_full.json').read_text());paired=json.loads((HERE/'full_parent.json').read_text());new=json.loads((HERE/'full_target.json').read_text())
 eligible=all(dominates_tasks(new,b) and retained_controls(new,b) and new['anchor_nll']<=b['anchor_nll']+1e-6 for b in [old,paired])
 baseline_style={r['id']:r for r in json.loads((HERE/'style_parent.json').read_text())['rows']};candidate_style=json.loads((HERE/'style_target.json').read_text())['rows']
 style_ok=all(not baseline_style[r['id']]['metrics']['structural_instruction_pass'] or r['metrics']['structural_instruction_pass'] for r in candidate_style)
 review=json.loads((HERE/'candidate_language_review.json').read_text());style_ok=style_ok and review['no_material_semantic_regression']
 save('full_decision.json',{'eligible_independent':bool(eligible and style_ok),'coding_general_retention_pass':eligible,'language_retention_pass':style_ok,'checkpoint_promoted':False})

@torch.inference_mode()
def validation(phase):
 if phase=='freeze':
  decision=json.loads((HERE/'full_decision.json').read_text());assert decision['eligible_independent']
  assert not (HERE/'validation_frozen.json').exists()
  save('validation_frozen.json',{'checkpoint_sha256':e.cr.file_hash(HERE/'checkpoints/target.pt'),'source_sha256':e.cr.file_hash(Path(__file__)),
   'data_sha256':e.DATA_HASH,'validation_ids':[r['id'] for r in e.DATA['validation']],'outputs_previously_observed':False});return
 frozen=json.loads((HERE/'validation_frozen.json').read_text());assert frozen['source_sha256']==e.cr.file_hash(Path(__file__))
 assert frozen['checkpoint_sha256']==e.cr.file_hash(HERE/'checkpoints/target.pt') and frozen['data_sha256']==e.DATA_HASH
 if phase=='select':
  reports={k:json.loads((HERE/f'validation_{k}.json').read_text()) for k in ['original','parent','target']}
  p=reports['parent'];n=reports['target'];accepted=dominates_tasks(n,p) and retained_controls(n,p) and n['anchor_nll']<=p['anchor_nll']+1e-6
  save('selection.json',{'selected':'target' if accepted else 'parent','checkpoint_promoted':accepted,'fresh_validation_consumed':True,
   'target_checkpoint':'loop012/checkpoints/target.pt' if accepted else None,'target_sha256':frozen['checkpoint_sha256'] if accepted else None,'parent_sha256':PARENT_HASH});return
 verify();state('validation_'+phase,True);m,t,meta=load_variant(phase);report={'status':'running','rows':[],'controls':[],'model':meta};name=f'validation_{phase}.json'
 for row in e.DATA['validation']:report['rows']+=e.coding(m,t,[row]);save(name,report)
 report['controls']=e.quality(m,t,e.DATA['controls']['val']);report['anchor_nll']=e.cr.likelihood(m,t,e.DATA['anchors'],anchors=True)['mean_nll'];report['status']='complete';save(name,report);state('validation_'+phase+'_complete')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['full_decide','freeze','original','parent','target','select']);a=p.parse_args()
 if a.phase=='full_decide':full_decide()
 else:validation(a.phase)
