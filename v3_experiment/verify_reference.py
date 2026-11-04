"""Check recovered base tensors against the original recorded functional probe."""
import json
from runtime import ROOT,HERE,load_teacher,tokenizer,atomic_json
from experiment import development_score


def main():
    previous=json.loads((ROOT/'v2_adaptation/teacher_development.json').read_text())
    model=load_teacher();actual=development_score(model,tokenizer())
    delta=actual['mean_answer_nll']-previous['mean_answer_nll']
    rows=[abs(a['answer_nll']-b['answer_nll']) for a,b in zip(actual['rows'],previous['rows'])]
    result={'original_recorded_nll':previous['mean_answer_nll'],'recovered_nll':actual['mean_answer_nll'],
        'mean_nll_delta':delta,'max_per_question_nll_delta':max(rows),
        'old_probe_only':True,'v3_heldout_used':False,
        'matches_previous_host_within_0p02':max(rows)<.02,
        'interpretation':'Recovered tensors are an algebraic reference. The safetensors file hash differs and these functional scores may differ from the previous host. Report this, do not mix historical scores with the new comparison.'}
    atomic_json(HERE/'reference_verification.json',result)
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':main()
