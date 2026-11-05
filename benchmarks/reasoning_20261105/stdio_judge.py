"""Credential-free stdin/stdout judge for the explicitly restricted LCB pilot."""
import ast
import builtins
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import types

ROOT=Path(__file__).resolve().parents[2]
ALLOWED_IMPORTS={'sys','math','collections','itertools','functools','heapq','bisect'}
FORBIDDEN={'eval','exec','compile','open','input_file','globals','locals','getattr','setattr','delattr','type','object','breakpoint','help','vars','dir'}
BUILTINS='range len str int float bool enumerate zip sum max min abs sorted reversed all any set dict list tuple round map filter isinstance ord chr divmod bin pow Exception ValueError IndexError TypeError EOFError StopIteration KeyError RuntimeError'.split()


def extract(text):
    if '</think>' in text:text=text.rsplit('</think>',1)[1]
    blocks=re.findall(r'```(?:python|py)?\s*\n(.*?)```',text,re.S|re.I)
    return (blocks[-1] if blocks else text).strip()


def validate(code):
    if len(code)>20000:raise ValueError('CodeLength')
    tree=ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node,(ast.ClassDef,ast.Global,ast.Nonlocal,ast.With,ast.AsyncWith,ast.AsyncFunctionDef)):
            raise ValueError('UnsupportedConstruct')
        if isinstance(node,ast.Name) and (node.id in FORBIDDEN or (node.id.startswith('_') and node.id!='__name__')):
            raise ValueError('UnsupportedName')
        if isinstance(node,ast.Attribute) and (node.attr.startswith('_') or node.attr in {'modules','path','environ','system','popen','fork','socket','open','load','loads','dump','dumps'}):
            raise ValueError('UnsupportedAttribute')
        if isinstance(node,ast.Import) and any(n.name not in ALLOWED_IMPORTS for n in node.names):
            raise ValueError('UnsupportedImport')
        if isinstance(node,ast.ImportFrom) and (node.level or node.module not in ALLOWED_IMPORTS or any(n.name.startswith('_') or n.name=='*' for n in node.names)):
            raise ValueError('UnsupportedImport')
        if isinstance(node,ast.FunctionDef) and node.decorator_list:
            raise ValueError('UnsupportedDecorator')
    return tree


def worker():
    import math,collections,itertools,functools,heapq,bisect
    modules={name:value for name,value in locals().items() if name in ALLOWED_IMPORTS}
    payload=json.load(sys.stdin)
    tree=validate(payload['code'])
    compiled=compile(tree,'<lcb-candidate>','exec')
    stdin=io.StringIO(payload['input']);stdin.buffer=io.BytesIO(payload['input'].encode())
    stdout=io.StringIO()
    def exit_(code=0):raise SystemExit(code)
    modules['sys']=types.SimpleNamespace(stdin=stdin,stdout=stdout,exit=exit_,setrecursionlimit=lambda n:sys.setrecursionlimit(min(int(n),10000)))
    def import_(name,globals=None,locals=None,fromlist=(),level=0):
        if level or name not in modules:raise ImportError('Only allowlisted modules')
        return modules[name]
    def print_(*args,sep=' ',end='\n',file=None,flush=False):
        if file not in (None,stdout):raise ValueError('Only stdout')
        stdout.write(sep.join(str(x) for x in args)+end)
    def input_(prompt=''):
        if prompt:stdout.write(str(prompt))
        line=stdin.readline()
        if not line:raise EOFError
        return line.rstrip('\n')
    env={'__name__':'__main__','__builtins__':{**{k:getattr(builtins,k) for k in BUILTINS},'__import__':import_,'print':print_,'input':input_}}
    spec=importlib.util.spec_from_file_location('lcb_seccomp',ROOT/'local_cpu/sandbox.py')
    safety=importlib.util.module_from_spec(spec);spec.loader.exec_module(safety)
    safety.restrict()
    try:
        exec(compiled,env)
        result={'status':'ok','stdout':stdout.getvalue()}
    except SystemExit as ex:
        result={'status':'ok' if ex.code in (0,None) else 'SystemExit','stdout':stdout.getvalue()}
    except BaseException as ex:
        result={'status':type(ex).__name__,'stdout':stdout.getvalue()}
    if len(result['stdout'])>1_000_000:result={'status':'OutputLimit','stdout':''}
    print(json.dumps(result),flush=True)


def run_case(code,stdin):
    with tempfile.TemporaryDirectory(prefix='liquid-lcb-') as cwd:
        p=subprocess.run([sys.executable,'-I','-S',str(Path(__file__).resolve()),'worker'],
            input=json.dumps({'code':code,'input':stdin}),text=True,capture_output=True,
            cwd=cwd,env={'LANG':'C.UTF-8'},timeout=5)
    if p.returncode in (-9,-11,-24):return {'status':'ResourceLimit','stdout':''}
    if p.returncode:raise RuntimeError('LCB judge infrastructure: '+p.stderr[-1000:])
    return json.loads(p.stdout)


def evaluate(text,oracle):
    code=extract(text);cases=oracle['cases'];bits=[];errors=[]
    try:validate(code)
    except (SyntaxError,ValueError) as ex:
        return {'case_passed':[False]*len(cases),'passed':0,'total':len(cases),'all_passed':False,
                'category':type(ex).__name__,'detail':str(ex),'code':code}
    for case in cases:
        try:r=run_case(code,case['input'])
        except subprocess.TimeoutExpired:r={'status':'Timeout','stdout':''}
        ok=r['status']=='ok' and r['stdout'].split()==case['output'].split()
        bits.append(ok)
        if not ok:errors.append(r['status'] if r['status']!='ok' else 'WrongStdout')
    return {'case_passed':bits,'passed':sum(bits),'total':len(bits),'all_passed':all(bits),
            'category':'passed' if all(bits) else errors[0],'error_types':sorted(set(errors)),'code':code}


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':worker()
    else:
        oracle={'cases':[{'input':'2 3\n','output':'5\n'},{'input':'-1 4\n','output':'3\n'}]}
        assert evaluate('import sys\na,b=map(int,sys.stdin.read().split())\nprint(a+b)',oracle)['all_passed']
        assert not evaluate('import os\nprint(os.listdir())',oracle)['all_passed']
        assert not evaluate('print(open("/etc/hostname").read())',oracle)['all_passed']
        assert run_case('import math\nprint(math.isqrt(int(input())))','25\n')['stdout']=='5\n'
        print('LCB_STDIO_JUDGE_PROBES_OK')
