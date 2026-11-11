"""Bounded serial orchestration; never promotes using an observed final test.

Use with the documented credential-free environment. Subprocess exit codes and
row files support resumption; do not blindly launch a second worker.
"""
import json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def command(script,*args):
    subprocess.run([sys.executable,str(HERE/script),*args],cwd=ROOT,check=True)

def main():
    command('teach.py','fit')
    command('check_mechanism.py')
    for kind in ['original','parent','loop','joint']:
        command('evaluate.py',kind,'screen')
        command('evaluate.py',kind,'controls')
        if kind in ['loop','joint']:command('evaluate.py',kind,'learning_diagnostic')
    parent=json.loads((HERE/'screen_parent.json').read_text())
    p={r['id']:r for r in parent['rows']};pc=json.loads((HERE/'controls_parent.json').read_text())
    cp={r['id']:r for r in pc['rows']};qual=[];audit={}
    for kind in ['loop','joint']:
        result=json.loads((HERE/('screen_'+kind+'.json')).read_text());c=json.loads((HERE/('controls_'+kind+'.json')).read_text())
        gains=[];losses=[];lost_cases=0
        for r in result['rows']:
            old=p[r['id']]
            if r['all_passed'] and not old['all_passed']:gains.append(r['id'])
            if old['all_passed'] and not r['all_passed']:losses.append(r['id'])
            lost_cases+=sum(a and not b for a,b in zip(old['case_passed'],r['case_passed']))
        control_losses=[r['id'] for r in c['rows'] if cp[r['id']]['correct'] and not r['correct']]
        nll_delta=c['language_anchor_nll']['mean_nll']-pc['language_anchor_nll']['mean_nll']
        okay=bool(gains) and not losses and not lost_cases and not control_losses and nll_delta<=.005
        audit[kind]={'task_gains':gains,'task_losses':losses,'lost_cases':lost_cases,'control_losses':control_losses,'anchor_nll_delta':nll_delta,'screen_passed':okay}
        if okay:qual.append(kind)
    selection={'stage':'screen','eligible_for_final_test':False,'selected':None,'checkpoint_promoted':False,'candidates':audit,
               'parent_retained':True,'final_test_evaluated':False,'validation_screen_tasks':8,'remaining_validation_tasks':32,'test_tasks_preserved':40}
    (HERE/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    if qual:
        # Explicit stop at a saved, reviewable phase; root researcher executes
        # preregistered full-validation and selection next, never tunes on test.
        selection['status']='screen_qualified_full_validation_required';selection['qualified']=qual
    else:selection['status']='complete_both_rejected_screen'
    (HERE/'selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    print('SELECTION',json.dumps(selection),flush=True)

if __name__=='__main__':main()
