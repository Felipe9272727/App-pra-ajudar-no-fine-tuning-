"""Check new problem text/signatures against persisted plain-text study sources."""
import json,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'balanced016'
def search(patterns,regex=False):
    args=['rg','-n','-i']+([] if regex else ['-F'])
    for glob in ['*.json','*.py','*.md','!balanced016/**']:args+=['--glob',glob]
    for pattern in patterns:args+=['-e',pattern]
    r=subprocess.run(args+['.'],cwd=ROOT,text=True,capture_output=True);assert r.returncode in (0,1),r.stderr
    return {'patterns':patterns,'returncode':r.returncode,'matches':r.stdout.splitlines()}
def main():
    code=json.loads((HERE/'validation_code.json').read_text());v2=json.loads((HERE/'validation_controls_v2.json').read_text())
    checks={'code_entry_names':search([r['entry_point'] for r in code]),'v2_control_exact_questions':search([r['question'] for r in v2]),'v2_new_facts_and_other_control_phrasings':search(['Ghana','Accra','tungsten','plural.{0,35}criterion','criterion.{0,35}plural','past.{0,35}cling','clung','Translate.{0,35}book','tradu.{0,35}livro','half of 62','8 vezes 9','Mara chegou antes'],True)}
    assert all(not x['matches'] for x in checks.values()),checks
    audit={'status':'passed_plain_text_novelty_screen','checks':checks,'scope':'Persisted .json/.py/.md sources under rg default ignore rules; excludes study016 itself. Does not prove absence from pretraining, compressed histories or all paraphrases. Ordinary skill-family overlap remains.','new_validation_model_queries_observed':0,'controls_version':'v2','original_v1_preserved':True,'code_tasks_unchanged':True,'candidate_weights_or_gates_changed':False}
    (HERE/'novelty_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':audit['status'],'checks':list(checks)}))
if __name__=='__main__':main()
