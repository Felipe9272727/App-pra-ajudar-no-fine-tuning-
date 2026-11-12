"""Correct legacy structural-probe training placeholders; leave scores/text unchanged."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'balanced016'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    import subprocess,re
    active=subprocess.run(['ps','-C','python','-o','args='],capture_output=True,text=True).stdout
    assert not re.search(r'python balanced016/(train|screen|validate|audit_weights)\.py',active)
    assert not (HERE/'metadata_correction.json').exists(), 'Inspect recorded correction before repeating'
    files=[]
    for name in ['training_complete.json','weight_audit.json','target_candidate.json','transfer_candidate.json','controls_candidate.json']:
        files.append((HERE/name,66))
    for variant,count in [('original',0),('principal',0),('E',50),('candidate',66)]:
        for role in ['code','controls']:
            p=HERE/('fresh_'+role+'_'+variant+'.json')
            if p.exists():files.append((p,count))
    changes=[]
    for p,count in files:
        before=sha(p);d=json.loads(p.read_text());owner=d['metadata'] if 'metadata' in d else d
        arch=owner.get('architecture')
        if arch is not None:
            prior=arch.get('backward_passes')
            owner['raw_structural_or_local_backward_count']=prior
            arch['backward_passes']=count
        owner['training_provenance']={'total_new_gradient_updates_in_recorded_lineage':count,'parent_specialist_E_updates':50 if count==66 else None,'gradient_updates_in_study016':16 if count==66 else 0,'structure_probe_default_is_not_a_training_history_measurement':True}
        p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
        changes.append({'path':str(p.relative_to(ROOT)),'before_sha256':before,'after_sha256':sha(p),'lineage_updates':count})
    correction={'type':'training_provenance_metadata_only','reason':'Historical check_architecture returns backward_passes=0 as a fixed structural placeholder. Study016 training initially reported16 local updates. Record66 total lineage updates (015B32+C6+D6+E6+01616), retaining raw counts separately.','generated_text_scores_tests_weights_and_inference_settings_unchanged':True,'files':changes}
    (HERE/'metadata_correction.json').write_text(json.dumps(correction,indent=2)+'\n');print(json.dumps(correction))
if __name__=='__main__':main()
