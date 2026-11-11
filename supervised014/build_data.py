"""Fixed complex algorithm subset, original public tests, disjoint datasets."""
import ast,gzip,hashlib,json
from pathlib import Path
from judge import evaluate
HERE=Path(__file__).resolve().parent
HUMAN=[32,39,75,114,119,129,132,147]
MBPP=[129,239,245,247,306,392,407,463]
INSTRUCTION='Return a complete Python implementation, with the required function name and any necessary helpers/imports. Return only Python code, no explanation or markdown.\n\n'

class StripDocs(ast.NodeTransformer):
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0],ast.Expr) and isinstance(node.body[0].value,ast.Constant) and isinstance(node.body[0].value.value,str):node.body.pop(0)
        return node

def normalized(code):return ast.unparse(ast.fix_missing_locations(StripDocs().visit(ast.parse(code))))+'\n'
def main():
    h={r['task_id']:r for r in [json.loads(l) for l in gzip.decompress((HERE/'sources/humaneval.jsonl.gz').read_bytes()).decode().splitlines()]}
    m={r['task_id']:r for r in json.loads((HERE/'sources/mbpp.json').read_text())}
    rows=[]
    for n in HUMAN:
        x=h['HumanEval/'+str(n)];solution=normalized(x['prompt']+x['canonical_solution'])
        rows.append({'id':x['task_id'],'benchmark':'humaneval','role':'taught','prompt':INSTRUCTION+x['prompt'],
            'solution':solution,'original_prompt':x['prompt'],'canonical_solution':x['canonical_solution'],
            'entry_point':x['entry_point'],'tests':[x['test']],'test_imports':[]})
    for n in MBPP:
        x=m[n];tree=ast.parse(x['code']);defs=[v for v in tree.body if isinstance(v,ast.FunctionDef)]
        calls={v.func.id for t in x['test_list'] for v in ast.walk(ast.parse(t)) if isinstance(v,ast.Call) and isinstance(v.func,ast.Name)}
        main=[v for v in defs if v.name in calls];assert len(main)==1,(n,calls)
        sig='def '+main[0].name+'('+ast.unparse(main[0].args)+'):'
        rows.append({'id':'MBPP/'+str(n),'benchmark':'mbpp','role':'transfer','prompt':INSTRUCTION+x['prompt']+'\nRequired signature: '+sig,
               'solution':x['code'],'entry_point':main[0].name,'tests':x['test_list'],'test_imports':x['test_imports']})
    audit=[]
    for r in rows:
        good=evaluate(r['solution'],r);assert good['all_passed'],(r['id'],good)
        bad=evaluate('def '+r['entry_point']+'(*args, **kwargs): return None',r);assert not bad['all_passed'],r['id']
        audit.append({'id':r['id'],'reference_passed':True,'none_mutant_rejected':True,'official_test_groups':good['total']})
    asts={role:{hashlib.sha256(ast.dump(ast.parse(r['solution'])).encode()).hexdigest() for r in rows if r['role']==role} for role in ['taught','transfer']}
    assert not asts['taught']&asts['transfer']
    for role in ['taught','transfer']:
        (HERE/(role+'.json')).write_text(json.dumps([r for r in rows if r['role']==role],indent=2)+'\n')
    report={'rows':audit,'taught':HUMAN,'transfer':MBPP,'exact_solution_ast_overlap':0,
            'official_tests_modified':False,'training_solution_format':'HumanEval full reference program with docstrings removed by AST, original canonical strings also preserved',
            'limitations':'Selected algorithmic pilot, not complete HumanEval/MBPP scores. MBPP is generally basic; selected longer DP/combinatorial tasks. Public pretraining contamination unknown.'}
    (HERE/'data_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
