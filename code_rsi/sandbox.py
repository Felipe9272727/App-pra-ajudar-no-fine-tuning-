"""Run generated functions in disposable containers without network or mounts."""
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ATTRS={'append','extend','pop','items','values','keys','get','count','index','split','join','lower','upper','strip','rstrip','lstrip','isdigit','isalpha','isalnum','sort','reverse','add','discard','remove','setdefault','copy','startswith','endswith','replace','update','clear','issubset','intersection','fromkeys','bit_count'}
BUILTINS=['range','len','str','int','float','bool','enumerate','zip','sum','max','min','abs','sorted','reversed','all','any','set','dict','list','tuple','round','map','filter','isinstance','ord','chr','divmod','bin','pow','Exception','ValueError','IndexError','TypeError']

def extract_code(text):
    # Strip explicit reasoning before parsing the final answer; never repair code.
    if '</think>' in text:text=text.rsplit('</think>',1)[1]
    elif '<think>' in text:return ''
    blocks=re.findall(r'```(?:python|py)?\s*\n(.*?)```',text,re.S|re.I)
    return (blocks[-1] if blocks else text).strip()


def check_ast(code):
    if len(code)>16000:raise ValueError('CodeLength')
    tree=ast.parse(code)
    if not tree.body or any(not isinstance(n,ast.FunctionDef) for n in tree.body):
        raise ValueError('FunctionDefinitionsOnly')
    if not any(n.name=='solve' for n in tree.body):raise ValueError('MissingSolve')
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom,ast.ClassDef,ast.Global,ast.Nonlocal,ast.With,ast.AsyncWith,ast.AsyncFunctionDef)):
            raise ValueError('UnsupportedConstruct')
        if isinstance(n,ast.FunctionDef) and n.decorator_list:raise ValueError('DecoratorsNotAllowed')
        if isinstance(n,ast.Name) and (n.id.startswith('_') or n.id in {'eval','exec','compile','open','input','globals','locals','getattr','setattr','delattr','type','object','print','help','breakpoint','exit','quit'}):
            raise ValueError('UnsupportedName')
        if isinstance(n,ast.Attribute) and n.attr not in ATTRS:raise ValueError('UnsupportedAttribute')
    return tree


def same_value(a,b):
    if isinstance(a,bool) or isinstance(b,bool):return type(a) is type(b) and a==b
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):return a==b
    if type(a) is not type(b):return False
    if isinstance(a,list):return len(a)==len(b) and all(same_value(x,y) for x,y in zip(a,b))
    if isinstance(a,dict):return a.keys()==b.keys() and all(same_value(a[k],b[k]) for k in a)
    return a==b


def execute_payload(payload):
    # This function is only run on generated model code inside the container.
    code=payload['code'];cases=payload['cases'];total=len(cases)
    try:tree=check_ast(code)
    except SyntaxError as e:return {'passed':0,'total':total,'all_passed':False,'category':'SyntaxError','line':e.lineno}
    except ValueError as e:return {'passed':0,'total':total,'all_passed':False,'category':'ContractError','detail':str(e)}
    import builtins
    env={'__builtins__':{k:getattr(builtins,k) for k in BUILTINS}}
    try:exec(compile(tree,'<candidate>','exec'),env)
    except Exception as e:return {'passed':0,'total':total,'all_passed':False,'category':type(e).__name__}
    passed=0;errors=[];case_passed=[]
    for case in cases:
        try:
            args=json.loads(json.dumps(case['args']))
            actual=env['solve'](*args)
            # Match JSON return conventions; do not award arbitrary truthy values.
            actual=json.loads(json.dumps(actual,allow_nan=False))
            ok=same_value(actual,case['expected']);case_passed.append(ok)
            if ok:passed+=1
            else:errors.append('WrongReturnValue')
        except Exception as e:errors.append(type(e).__name__);case_passed.append(False)
    return {'passed':passed,'total':total,'all_passed':passed==total,
        'category':'passed' if passed==total else (errors[0] if errors else 'WrongReturnValue'),
        'error_types':sorted(set(errors)),'case_passed':case_passed}


def evaluate(text,task):
    code=extract_code(text);total=len(task['cases'])
    try:check_ast(code)
    except SyntaxError as e:return {'passed':0,'total':total,'all_passed':False,'category':'SyntaxError','line':e.lineno,'code':code}
    except ValueError as e:return {'passed':0,'total':total,'all_passed':False,'category':'ContractError','detail':str(e),'code':code}
    image=os.environ['CODE_IMAGE']
    if not re.fullmatch(r'(?:docker.io/library/)?python@sha256:[0-9a-f]{64}',image):raise RuntimeError('Require the exact prepared Python image digest')
    name='liquid-code-'+uuid.uuid4().hex
    source=Path(__file__).read_text()
    cmd=['docker','run','--rm','-i','--name',name,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--pids-limit','32','--memory','128m','--cpus','1','--user','65534:65534',image,'python','-I','-S','-c',source]
    try:
        result=subprocess.run(cmd,input=json.dumps({'code':code,'cases':task['cases']}),text=True,capture_output=True,timeout=12)
        if result.returncode in [137,139]:
            report={'passed':0,'total':total,'all_passed':False,'category':'ResourceLimit'}
        elif result.returncode:raise RuntimeError('Sandbox infrastructure failed: '+result.stderr[-500:])
        else:report=json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        report={'passed':0,'total':total,'all_passed':False,'category':'Timeout'}
    finally:
        subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
    return {**report,'code':code}

if __name__=='__main__':
    data=json.load(sys.stdin)
    print(json.dumps(execute_payload(data)))
