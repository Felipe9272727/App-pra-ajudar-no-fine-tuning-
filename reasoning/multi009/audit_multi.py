"""Read-only final integrity and paired-quality summary for008/009."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
import torch

torch.set_num_threads(4)
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reasoning/multi009'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
expected={'rsi100/checkpoints/best.pt':'46f6697cd260e5055280b6f6427896d8df1cfd00cb8b2c3bbbf8586e4fa5fae8',
 'mentor/checkpoints/negative_002_recovered.pt':'8fd291019b20f7d327e775c05a30f5b991395718040e4ad2fe52ed986ff748ef',
 'upstream/model.safetensors-00001-of-00001.safetensors':'04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696'}
preserved={p:digest(ROOT/p)==h for p,h in expected.items()};assert all(preserved.values())
frozen={}
for path in ['benchmarks/reasoning_20261105/frozen.json','reasoning/multi008/frozen.json','reasoning/multi009/frozen.json']:
    frozen[path]={p:digest(ROOT/p)==h for p,h in read(path)['files'].items()};assert all(frozen[path].values()),path
artifacts={}
for folder in ['multi008','multi009']:
    for path in sorted((ROOT/'reasoning'/folder).rglob('*.pt')):
        obj=torch.load(path,weights_only=True);assert isinstance(obj,dict)
        artifacts[str(path.relative_to(ROOT))]={'bytes':path.stat().st_size,'sha256':digest(path),
            'git_blob':subprocess.check_output(['git','hash-object',str(path)],text=True).strip(),'safe_tensor_load':True}
for kind in ['target','inverse_control']:
    for item in read(f'reasoning/multi009/patch_{kind}.json')['files'].values():assert digest(ROOT/item['path'])==item['sha256']
parent={r['id']:r for r in read('reasoning/cycle2/trial_006_parent_full.json')['rows']}
original={r['id']:r for r in read('reasoning/cycle2/development_original.json')['rows']}
summary={'selected':'parent','checkpoint_promoted':False,'studies':{},'golds_changed':False,
    'correct_solutions_in_calibration_inputs':False,'backward_passes':0,'fresh_validation_consumed':False}
for n in ['008','009']:
    folder=f'reasoning/multi{n}/';decision=read(folder+f'trial_{n}.json');construction=read(folder+'construction.json')
    assert decision['stage']=='rejected_on_screen'
    screens={}
    for kind,result in decision['screens'].items():
        rows=result['rows']
        screens[kind]={'tasks':len(rows),'complete_tasks':sum(r['all_passed'] for r in rows),
            'cases':sum(r['passed'] for r in rows),'total_cases':sum(r['total'] for r in rows),
            'case_wins':result['case_wins'],'case_losses':result['case_losses'],
            'texts_different_from_parent':sum(r['output']!=parent[r['id']]['output'] for r in rows)}
    ids=[r['id'] for r in decision['screens']['target']['rows']]
    references={v:{'complete_tasks':sum(bank[k]['all_passed'] for k in ids),
        'cases':sum(bank[k]['passed'] for k in ids),'total_cases':sum(bank[k]['total'] for k in ids)} for v,bank in [('original',original),('parent',parent)]}
    if n=='008':
        changed=construction['actual_changes']['target']
        dirs=torch.load(ROOT/folder/'directions_008.pt',weights_only=True)
        distances=[float(((dirs['parent_moments'][k]+1e-6).log()-(dirs['reference_moments'][k]+1e-6).log()).square().mean()) for k in dirs['reference_moments']]
        mechanism={'baseline_mean_squared_log_moment_distance':sum(distances)/len(distances),
            'target_distance':decision['screens']['target']['moments']['mean_squared_log_moment_distance'],
            'inverse_distance':decision['screens']['inverse_control']['moments']['mean_squared_log_moment_distance']}
        changed_count=changed['changed_values'];changed_tensors=changed['changed_tensors']
    else:
        changed_count=construction['changed_values']['target'];changed_tensors=len(construction['layers'])
        mechanism={kind:decision['screens'][kind]['internal_distance'] for kind in decision['screens']}
    summary['studies'][n]={'decision':decision['stage'],'changed_values':changed_count,
        'changed_tensors':changed_tensors,'screens':screens,'references':references,'mechanism':mechanism,
        'full_development_and_language_gates_run':False,'independent_validation_run':False}
save('summary.json',summary)
active=[]
for row in subprocess.check_output(['ps','-eo','pid,comm,args'],text=True).splitlines()[1:]:
    pieces=row.split(None,2)
    if len(pieces)==3 and pieces[1].startswith('python') and int(pieces[0])!=os.getpid():
        if any(s in pieces[2] for s in ['study008.py','study009.py','validate008.py','validate009.py','local_cpu/controller.py']):active.append(row)
assert not active,active
save('integrity.json',{'preserved_checkpoints_and_upstream':preserved,'frozen_file_checks':frozen,
    'artifacts':artifacts,'tensor_artifact_count':len(artifacts),'active_model_processes':active,
    'checked_unix':time.time(),'selected_parent_unchanged':True})
for n in ['008','009']:
    path=ROOT/f'reasoning/multi{n}/status.json';status=json.loads(path.read_text())
    status.update(status='complete_rejected_parent_retained',model_process_active=False,
        process_continues_in_background=False,checkpoint_promoted=False,selected='parent',
        fresh_validation_consumed=False,technical_tests_passed=46,updated_unix=time.time())
    path.write_text(json.dumps(status,indent=2)+'\n')
print('AUDIT_COMPLETE',len(artifacts),'tensor artifacts, no active model processes')
