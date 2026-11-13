"""Real Android ARM64 shared interpreter; official NDK API28 headers/stubs."""
import os,subprocess,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=Path('/dev/shm/liquid-android/tools022');PACKAGE=BASE/'python-host/micropython_embed';OUT=BASE/'python-arm';OUT.mkdir(exist_ok=True)
def main():
 env={**os.environ,'ZIG_GLOBAL_CACHE_DIR':str(BASE/'zig-cache'),'ZIG_LOCAL_CACHE_DIR':str(BASE/'zig-local')};sdk=Path('/dev/shm/liquid-android/tooling/android/sysroot')
 cc=[str(BASE/'zig-linux-x86_64-0.13.0/zig'),'cc','-target','aarch64-linux-android','-nostdlib','-fPIC','-O2','-DNDEBUG','-D__ANDROID_API__=28','-I'+str(sdk/'include'),'-I'+str(sdk/'include/aarch64-linux-android'),'-I'+str(BASE/'python-host'),'-I'+str(PACKAGE),'-I'+str(PACKAGE/'port')]
 sources=list((PACKAGE/'py').glob('*.c'))+list((PACKAGE/'port').glob('*.c'))+list((PACKAGE/'shared/runtime').glob('*.c'))+list((PACKAGE/'extmod').glob('*.c'))+[ROOT/'tooluse022/python_port/runner.c'];objects=[]
 for s in sources:
  if s.name=='mphalport.c':continue
  obj=OUT/(s.stem+'.o')
  if '--link-only' not in sys.argv:subprocess.run([*cc,'-c',str(s),'-o',str(obj)],check=True,env=env)
  assert obj.exists();objects.append(str(obj))
 lib=OUT/'libliquid_python.so';subprocess.run([*cc,'-shared',*objects,str(sdk/'28/libc.so'),str(sdk/'28/libm.so'),str(sdk/'28/libdl.so'),'-Wl,-z,max-page-size=16384','-Wl,--no-undefined','-o',str(lib)],check=True,env=env)
 report={'status':'ARM64_interpreter_compiled','bytes':lib.stat().st_size,'sha256':hashlib.sha256(lib.read_bytes()).hexdigest(),'Android_API':28,'MICROPYTHON':'1.26.1','heap_bytes':16*1024*1024,'max_VM_hooks':2000000,'wall_seconds_VM':2,'phone_execution_verified':False,'filesystem_network_process_bindings':False}
 (ROOT/'tooluse022/reports/python_arm_build.json').write_text(json.dumps(report,indent=2)+'\n');print('PYTHON_ARM_BUILT',flush=True)
if __name__=='__main__':main()
