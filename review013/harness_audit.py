"""Read-only audit; never alter judge, model outputs, scores or selection."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT))
from local_cpu.sandbox import evaluate

def main():
    cases=[{'args':[[]],'expected':[]},{'args':[[3]],'expected':[1]},{'args':[[7,8]],'expected':[1,1]}]
    codes={'ordinary_name':'def solve(xs): return [1 for item in xs]',
           'single_underscore':'def solve(xs): return [1 for _ in xs]'}
    scores={k:evaluate(v,{'cases':cases}) for k,v in codes.items()}
    assert scores['ordinary_name']['all_passed']
    assert scores['single_underscore']['category']=='ContractError' and scores['single_underscore']['detail']=='UnsupportedName'
    report={'status':'frozen_judge_construct_bias_confirmed','probes':scores,
       'judging_policy_modified':False,'model_outputs_repaired':False,'model_scores_replaced':False,
       'selection_changed':False,'interpretation':'Single underscore is valid local Python. Do not equate this construct rejection with semantic error or intelligence loss. Preserve preregistered primary scores.'}
    (HERE/'harness_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
