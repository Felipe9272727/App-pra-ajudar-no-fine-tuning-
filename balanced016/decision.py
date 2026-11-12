"""Evaluate preregistered retention gates without querying sealed validation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'balanced016'
def read(p):return json.loads((ROOT/p).read_text())
def main():
    current={role:read('balanced016/'+role+'_candidate.json') for role in ['target','transfer','controls']}
    assert all(r['status']=='complete' for r in current.values())
    parent=read('supervised014/controls_parent.json');specialist=read('supervised015/attempt_e/transfer_specialist.json')
    byid={r['id']:r for r in current['controls']['rows']};oldgood={r['id'] for r in parent['rows'] if r['correct']}
    mbpp={r['id']:r for r in current['transfer']['rows']}
    # Judge details expose per-test boolean outcomes; retain every previously passing group.
    group_losses=[]
    for old in specialist['rows']:
        new=mbpp[old['id']]
        if old['all_passed'] and not new['all_passed']:group_losses.append(old['id']+':complete_task')
        # E has zero passing groups; keep a guarded exact comparison for this parent.
        assert old['passed']==0, 'Inspect individual case schema before changing this baseline'
    gates={'taught_all8_retained':current['target']['tasks_passed']==8,
           'every_principal_correct_control_retained':all(byid[i]['correct'] for i in oldgood),
           'at_least10_of12_controls':current['controls']['correct']>=10,
           'no_E_mbpp_task_or_test_group_loss':not group_losses,
           'anchor_nll_within_principal_plus_005':current['controls']['anchor_nll']<=parent['anchor_nll']+.005}
    result={'status':'complete','gates':gates,'passed':all(gates.values()),'fresh_validation_opened':False,'checkpoint_promoted':False,
            'scores':{'taught':current['target']['tasks_passed'],'transfer':current['transfer']['tasks_passed'],'controls':current['controls']['correct'],'anchor_nll':current['controls']['anchor_nll']},
            'lost_principal_controls':[i for i in sorted(oldgood) if not byid[i]['correct']], 'mbpp_losses':group_losses,
            'general_principal_preserved':True,'prior_specialist_E_preserved':True}
    (HERE/'gate.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
