"""Apply unchanged screen gates to completed raw outputs; zero model calls.

Postprocessing recovery: canonical syntax/AST early rejection has no per-case
array. Infer zero SCORE bits only for these documented zero-score rejections.
Raw judge outputs, scores, prompts, weights and frozen source remain untouched.
"""
import hashlib,json
from pathlib import Path
from case_bits import scored_case_bits
HERE=Path(__file__).resolve().parent
def read(n):return json.loads((HERE/n).read_text())
def main():
    parent=read('screen_parent.json');pc=read('controls_parent.json');p={r['id']:r for r in parent['rows']};cp={r['id']:r for r in pc['rows']}
    audit={};qual=[];derived={}
    for kind in ['original','parent','loop','joint']:
        s=read('screen_'+kind+'.json');c=read('controls_'+kind+'.json')
        assert s['status']==c['status']=='complete'
        assert s['frozen_sha256']==hashlib.sha256((HERE/'frozen.json').read_bytes()).hexdigest()
        derived[kind]=[r['id'] for r in s['rows'] if 'case_passed' not in r]
        for r in s['rows']:scored_case_bits(r)
    for kind in ['loop','joint']:
        result=read('screen_'+kind+'.json');c=read('controls_'+kind+'.json');gains=[];losses=[];lost_cases=0
        assert read('learning_diagnostic_'+kind+'.json')['status']=='complete'
        for r in result['rows']:
            old=p[r['id']]
            if r['all_passed'] and not old['all_passed']:gains.append(r['id'])
            if old['all_passed'] and not r['all_passed']:losses.append(r['id'])
            lost_cases+=sum(a and not b for a,b in zip(scored_case_bits(old),scored_case_bits(r)))
        control_losses=[r['id'] for r in c['rows'] if cp[r['id']]['correct'] and not r['correct']]
        nll_delta=c['language_anchor_nll']['mean_nll']-pc['language_anchor_nll']['mean_nll']
        okay=bool(gains) and not losses and not lost_cases and not control_losses and nll_delta<=.005
        audit[kind]={'task_gains':gains,'task_losses':losses,'lost_cases':lost_cases,'control_losses':control_losses,'anchor_nll_delta':nll_delta,'screen_passed':okay}
        if okay:qual.append(kind)
    selection={'stage':'screen','eligible_for_final_test':False,'selected':None,'checkpoint_promoted':False,'candidates':audit,
          'parent_retained':True,'final_test_evaluated':False,'validation_screen_tasks':8,'remaining_validation_tasks':32,'test_tasks_preserved':40,
          'status':'screen_qualified_full_validation_required' if qual else 'complete_both_rejected_screen',
          'aggregation_recovery':'Missing score bits for zero-score pre-execution SyntaxError/ContractError only; no score or criterion changed',
          'rows_with_derived_zero_score_bits':derived}
    if qual:selection['qualified']=qual
    (HERE/'selection.json').write_text(json.dumps(selection,indent=2)+'\n');print(json.dumps(selection,indent=2))
if __name__=='__main__':main()
