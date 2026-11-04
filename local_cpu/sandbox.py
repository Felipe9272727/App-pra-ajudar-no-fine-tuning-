"""Credential-free, syscall-filtered subprocess for the existing coding judge.

Docker is unavailable in the local environment. The child preloads the same AST
judge, then clears capabilities, applies resource limits and denies syscall access
before executing code. UID/GID are dropped when the host permits that operation.
This is recorded as a distinct execution environment, never a Docker result.
"""
import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def restrict():
    import ctypes,resource
    lib=ctypes.CDLL('libseccomp.so.2',use_errno=True)
    lib.seccomp_init.argtypes=[ctypes.c_uint32];lib.seccomp_init.restype=ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];lib.seccomp_syscall_resolve_name.restype=ctypes.c_int
    lib.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
    lib.seccomp_load.argtypes=[ctypes.c_void_p];lib.seccomp_release.argtypes=[ctypes.c_void_p]
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(38,1,0,0,0):raise OSError(ctypes.get_errno(),'no_new_privs')
    for kind,limit in [(resource.RLIMIT_CPU,2),(resource.RLIMIT_AS,128*1024*1024),
                       (resource.RLIMIT_CORE,0),(resource.RLIMIT_FSIZE,0),
                       (resource.RLIMIT_NOFILE,16),(resource.RLIMIT_NPROC,1)]:
        resource.setrlimit(kind,(limit,limit))
    if os.getuid()==0:
        try:
            os.setgroups([]);os.setgid(65534);os.setuid(65534)
        except PermissionError:
            # Some managed containers expose UID 0 without SETUID/SETGID.
            # Clear all capabilities and still enforce the deny-by-default
            # filter; never execute a payload if capability clearing fails.
            pass
    class Header(ctypes.Structure):
        _fields_=[('version',ctypes.c_uint32),('pid',ctypes.c_int)]
    class Caps(ctypes.Structure):
        _fields_=[('effective',ctypes.c_uint32),('permitted',ctypes.c_uint32),('inheritable',ctypes.c_uint32)]
    header=Header(0x20080522,0);caps=(Caps*2)()
    if libc.capset(ctypes.byref(header),ctypes.byref(caps)):raise OSError(ctypes.get_errno(),'capset')
    status=Path('/proc/self/status').read_text().splitlines()
    assert all(int(line.split()[1],16)==0 for line in status if line.startswith(('CapEff:','CapPrm:','CapInh:')))
    ctx=lib.seccomp_init(0x00050000|1) # EPERM for every syscall not allowed.
    if not ctx:raise RuntimeError('seccomp_init failed')
    try:
        calls='read write close fstat lseek mmap mprotect munmap brk mremap madvise futex clock_gettime clock_getres rt_sigaction rt_sigprocmask rt_sigreturn sigaltstack getpid gettid getrandom sched_yield exit exit_group'
        for name in calls.split():
            nr=lib.seccomp_syscall_resolve_name(name.encode())
            if nr<0 or lib.seccomp_rule_add(ctx,0x7fff0000,nr,0):raise RuntimeError('seccomp rule '+name)
        if lib.seccomp_load(ctx):raise OSError(ctypes.get_errno(),'seccomp_load')
    finally:lib.seccomp_release(ctx)

def worker():
    import importlib.util,socket
    spec=importlib.util.spec_from_file_location('canonical_judge',ROOT/'code_rsi/sandbox.py')
    judge=importlib.util.module_from_spec(spec);spec.loader.exec_module(judge)
    payload=json.load(sys.stdin)
    restrict()
    if payload.get('probe'):
        denied={}
        for key,fn in [('filesystem',lambda:os.open('/etc/hostname',os.O_RDONLY)),
                       ('network',lambda:socket.socket()),('process',lambda:os.fork())]:
            try:fn();denied[key]=False
            except PermissionError:denied[key]=True
        result={'denied':denied,'capabilities_cleared':True}
    else:result=judge.execute_payload(payload)
    print(json.dumps(result),flush=True)

def run(payload,timeout=8):
    with tempfile.TemporaryDirectory(prefix='liquid-local-judge-') as cwd:
        os.chmod(cwd,0o755)
        p=subprocess.run([sys.executable,'-I','-S',str(Path(__file__).resolve()),'worker'],
          input=json.dumps(payload),text=True,capture_output=True,cwd=cwd,
          env={'LANG':'C.UTF-8'},timeout=timeout)
    if p.returncode in (-9,-11,-24) and 'cases' in payload:
        total=len(payload['cases'])
        return {'passed':0,'total':total,'all_passed':False,'category':'ResourceLimit','case_passed':[False]*total}
    if p.returncode:raise RuntimeError('Local judge process failed: '+p.stderr[-1000:])
    return json.loads(p.stdout)

def evaluate(text,task):
    # Same extraction, AST policy, cases and comparisons as the Docker judge.
    import importlib.util
    spec=importlib.util.spec_from_file_location('canonical_judge_parent',ROOT/'code_rsi/sandbox.py')
    judge=importlib.util.module_from_spec(spec);spec.loader.exec_module(judge)
    code=judge.extract_code(text)
    try:result=run({'code':code,'cases':task['cases']})
    except subprocess.TimeoutExpired:
        result={'passed':0,'total':len(task['cases']),'all_passed':False,'category':'Timeout','case_passed':[False]*len(task['cases'])}
    return {**result,'code':code}

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='worker':worker()
    else:
        assert run({'probe':True})=={'denied':{'filesystem':True,'network':True,'process':True},'capabilities_cleared':True}
        ok=evaluate('def solve(xs): return sum(xs)',{'cases':[{'args':[[2,3]],'expected':5}]})
        assert ok['all_passed'] and ok['case_passed']==[True],ok
        bad=evaluate('def solve(xs): return len(xs)',{'cases':[{'args':[[2,3]],'expected':5}]})
        assert bad['case_passed']==[False],bad
        print('LOCAL_SANDBOX_PROBES_OK')
