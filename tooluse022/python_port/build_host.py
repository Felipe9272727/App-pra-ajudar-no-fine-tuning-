"""Build a minimal no-I/O interpreter from pinned official source."""
import subprocess,shutil,json,hashlib,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PORT=ROOT/'tooluse022/python_port';OUT=Path('/dev/shm/liquid-android/tools022/python-host');MP=Path('/dev/shm/liquid-android/tools022/micropython-1.26.1')
def main():
 OUT.mkdir(exist_ok=True);shutil.copy(PORT/'mpconfigport.h',OUT/'mpconfigport.h');shutil.copy(PORT/'embed.mk',OUT/'embed.mk')
 subprocess.run(['make','-f','embed.mk','-j2'],cwd=OUT,check=True)
 package=OUT/'micropython_embed';shutil.copy(MP/'extmod/modjson.c',package/'extmod/modjson.c')
 sources=list((package/'py').glob('*.c'))+list((package/'port').glob('*.c'))+list((package/'shared/runtime').glob('*.c'))+list((package/'extmod').glob('*.c'))
 sources=[s for s in sources if s.name!='mphalport.c'];objects=[]
 flags=['-O2','-std=gnu99','-DNDEBUG','-D_POSIX_C_SOURCE=200809L','-I'+str(OUT),'-I'+str(package),'-I'+str(package/'port')]
 for s in sources+[PORT/'runner.c']:
  obj=OUT/(s.stem+'.o');subprocess.run(['cc',*flags,'-c',str(s),'-o',str(obj)],check=True);objects.append(str(obj))
 subprocess.run(['cc',*objects,'-lm','-o',str(OUT/'liquid-python')],check=True)
 print('PYTHON_HOST_BUILT',flush=True)
if __name__=='__main__':main()
