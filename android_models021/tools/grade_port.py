"""Port verification only on previously observed data; frozen old judges/golds."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));HERE=ROOT/'android_models021'
from supervised014.judge import evaluate
from code_rsi.runtime import grade

def main():
 outputs=json.loads((HERE/'reports/native_outputs.json').read_text());targets={r['id']:r for r in json.loads((ROOT/'supervised015/attempt_e/train.json').read_text())};controls={r['id']:r for r in json.loads((ROOT/'review013/controls.json').read_text())};taught=[];general=[]
 for r in outputs:
  if r['id'] in targets:taught.append({**r,**evaluate(r['output'],targets[r['id']])})
  else:general.append({**r,'correct':grade(r['output'],controls[r['id']])[0]})
 report={'status':'complete' if len(outputs)==20 else 'in_progress','purpose':'deployment_port_verification_not_new_training_or_independent_benchmark','source_checkpoint':'015E','new_gradient_updates':0,'source_PyTorch_taught_score':8,'native_taught_passed':sum(r['all_passed'] for r in taught),'native_taught_completed':len(taught),'native_taught_total':8,'source_PyTorch_controls':6,'native_controls_correct':sum(r['correct'] for r in general),'native_controls_completed':len(general),'native_controls_total':12,'protocol':{'same_source_input_token_ids':True,'only_problem_in_inputs':True,'reference_solutions_tests_not_in_inputs':True,'greedy':True,'thinking':False,'native_eos':248044,'code_budget':320,'controls_budget':64,'threads':4,'hardware':'cloud_x86_not_physical_ARM_phone','source_weights_all546_exactly_verified':True},'taught':taught,'controls':general}
 (HERE/'reports/native_fidelity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','native_taught_passed','native_taught_completed','native_controls_correct','native_controls_completed']}))
if __name__=='__main__':main()
