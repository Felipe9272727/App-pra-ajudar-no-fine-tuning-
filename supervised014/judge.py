"""Official function tests in the existing credential-free seccomp sandbox.

Separate candidate/test namespaces, supported stdlib imports, and single local
underscores accepted. Tests are not rewritten or exposed to model generation.
"""
import ast,builtins,importlib,importlib.util,io,json,re,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MODULES='math re collections itertools functools heapq bisect typing string statistics fractions decimal operator random copy'.split()
NAMES='abs all any ascii bin bool bytearray bytes callable chr complex dict divmod enumerate filter float format frozenset hash hex int isinstance issubclass iter len list map max min next oct ord pow range repr reversed round set slice sorted str sum tuple zip Exception ValueError TypeError IndexError KeyError StopIteration ZeroDivisionError AssertionError NotImplementedError RuntimeError'.split()
FORBIDDEN={'open','eval','exec','compile','globals','locals','vars','dir','getattr','setattr','delattr','breakpoint','help','input'}

def extract(text):
    if '</think>' in text:text=text.rsplit('</think>',1)[1]
    blocks=re.findall(r'```(?:python|py)?\s*\n(.*?)```',text,re.S|re.I)
    return (blocks[-1] if blocks else text).strip()

def validate(code):
    if len(code)>50000:raise ValueError('CodeLength')
    tree=ast.parse(code)
    for n in ast.walk(tree):
        if isinstance(n,(ast.ClassDef,ast.AsyncFunctionDef,ast.With,ast.AsyncWith,ast.Global,ast.Nonlocal)):raise ValueError('UnsupportedConstruct')
        if isinstance(n,ast.Name) and (n.id in FORBIDDEN or (n.id.startswith('__') and n.id!='__name__')):raise ValueError('UnsupportedName')
        if isinstance(n,ast.Attribute) and (n.attr.startswith('_') or n.attr in {'environ','modules','system','popen','fork','socket','open','load','loads','dump','dumps'}):raise ValueError('UnsupportedAttribute')
        if isinstance(n,ast.Import) and any(x.name not in MODULES for x in n.names):raise ValueError('UnsupportedImport')
        if isinstance(n,ast.ImportFrom) and (n.level or n.module not in MODULES or any(x.name.startswith('_') or x.name=='*' for x in n.names)):raise ValueError('UnsupportedImport')
        if isinstance(n,ast.FunctionDef) and n.decorator_list:raise ValueError('UnsupportedDecorator')
    return tree

def worker():
    modules={k:importlib.import_module(k) for k in MODULES}
    payload=json.load(sys.stdin)
    try:compiled=compile(validate(payload['code']),'<candidate>','exec')
    except (SyntaxError,ValueError) as ex:
        print(json.dumps({'all_passed':False,'category':type(ex).__name__,'detail':str(ex),'case_passed':[False]*len(payload['tests'])}));return
    compiled_tests=[compile(t,'<official-test>','exec') for t in payload['tests']]
    setup=compile(payload.get('setup',''),'<public-problem-prefix>','exec')
    imports=[compile(t,'<official-import>','exec') for t in payload.get('test_imports',[])]
    def guarded_import(name,globals=None,locals=None,fromlist=(),level=0):
        if level or name not in modules:raise ImportError('Only declared standard library')
        return modules[name]
    output=io.StringIO()
    def print_(*a,sep=' ',end='\n',**kw):
        if output.tell()>100000:raise ValueError('OutputLimit')
        output.write(sep.join(str(x) for x in a)+end)
    safe={**{k:getattr(builtins,k) for k in NAMES},'__import__':guarded_import,'print':print_}
    env={'__builtins__':safe,'__name__':'benchmark_candidate'}
    spec=importlib.util.spec_from_file_location('secure_benchmark',ROOT/'local_cpu/sandbox.py')
    security=importlib.util.module_from_spec(spec);spec.loader.exec_module(security)
    security.restrict()
    # HumanEval supplies imports/helpers in its public prefix, before completion.
    exec(setup,env)
    modules['random'].seed(0)
    bits=[];errors=[]
    try:exec(compiled,env)
    except BaseException as ex:
        bits=[False]*len(compiled_tests);errors=[type(ex).__name__]
    else:
        # Tests cannot be shadowed by a model-defined check() or its globals.
        test_env={'__builtins__':safe}
        exec(setup,test_env)
        if payload['benchmark']=='mbpp':test_env.update({k:v for k,v in env.items() if k!='__builtins__'})
        for code in imports:exec(code,test_env)
        for code in compiled_tests:
            try:
                exec(code,test_env)
                if payload['benchmark']=='humaneval':test_env['check'](env[payload['entry_point']])
                bits.append(True)
            except BaseException as ex:bits.append(False);errors.append(type(ex).__name__)
    print(json.dumps({'all_passed':all(bits),'case_passed':bits,'category':'passed' if all(bits) else errors[0],'error_types':sorted(set(errors))}),flush=True)

def evaluate(text,row):
    code=extract(text)
    with tempfile.TemporaryDirectory(prefix='liquid-benchmark-') as cwd:
        try:
            p=subprocess.run([sys.executable,'-I','-S',str(Path(__file__).resolve()),'worker'],
                input=json.dumps({'code':code,'setup':row.get('original_prompt',''),**{k:row[k] for k in ['benchmark','tests','entry_point','test_imports']}}),
                text=True,capture_output=True,cwd=cwd,env={'LANG':'C.UTF-8'},timeout=8)
            if p.returncode in [-9,-11,-24]:result={'all_passed':False,'case_passed':[False]*len(row['tests']),'category':'ResourceLimit'}
            elif p.returncode:raise RuntimeError('Judge infrastructure: '+p.stderr[-1500:])
            else:result=json.loads(p.stdout)
        except subprocess.TimeoutExpired:result={'all_passed':False,'case_passed':[False]*len(row['tests']),'category':'Timeout'}
    result.update(code=code,passed=sum(result['case_passed']),total=len(row['tests']));return result

if __name__=='__main__':worker()
