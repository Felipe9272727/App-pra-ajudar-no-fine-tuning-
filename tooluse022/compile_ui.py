"""Verify Android resources, Java/JNI declarations and real DEX without new APK."""
import json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'tooluse022';SDK=Path('/dev/shm/liquid-android/tooling/android');BT=SDK/'build-tools';OUT=Path('/dev/shm/liquid-android/tools022/ui');OUT.mkdir(exist_ok=True);SOURCE=HERE/'android';ENV={**os.environ,'LD_LIBRARY_PATH':str(BT/'lib64'),'JAVA_TOOL_OPTIONS':'-Xmx384m'}
def run(*a):subprocess.run([str(x) for x in a],check=True,env=ENV)
run(BT/'aapt2','compile','--dir',SOURCE/'res','-o',OUT/'resources.zip');gen=OUT/'generated';gen.mkdir(exist_ok=True)
run(BT/'aapt2','link','-o',OUT/'resources.apk','--manifest',SOURCE/'AndroidManifest.xml','-I',SDK/'platform/android.jar','-R',OUT/'resources.zip','--java',gen,'--custom-package','dev.liquidsense.chat','--auto-add-overlay');classes=OUT/'classes';classes.mkdir(exist_ok=True)
run('java','com.sun.tools.javac.Main','-source','8','-target','8','-classpath',SDK/'platform/android.jar','-d',classes,*SOURCE.glob('src/**/*.java'),*gen.rglob('*.java'));dex=OUT/'dex';dex.mkdir(exist_ok=True)
run('java','-cp',BT/'lib/d8.jar','com.android.tools.r8.D8','--min-api','28','--lib',SDK/'platform/android.jar','--output',dex,*classes.rglob('*.class'));print('ANDROID_TOOLS_UI_DEX_COMPILED',flush=True)
