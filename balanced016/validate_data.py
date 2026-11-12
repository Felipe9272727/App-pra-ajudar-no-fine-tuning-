"""Validate frozen reference programs and reject always-None mutants; no model call."""
import json
from pathlib import Path
from judge import evaluate
HERE=Path(__file__).resolve().parent
def main():
    out=[]
    for row in json.loads((HERE/'validation_code.json').read_text()):
        reference=evaluate(row['solution'],row);mutant=evaluate(row['signature']+':\n    return None\n',row)
        assert reference['all_passed'],(row['id'],reference)
        assert not mutant['all_passed'],(row['id'],mutant)
        out.append({'id':row['id'],'reference_passed':True,'None_mutant_rejected':True,'test_groups':reference['total']})
    (HERE/'reference_audit.json').write_text(json.dumps(out,indent=2)+'\n');print('validated',len(out),'references and',len(out),'mutants')
if __name__=='__main__':main()
