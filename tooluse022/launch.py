"""Credential-free model launcher; pass only nonsecret public-web proxy/CA config."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
env={'PATH':'/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin:/usr/bin:/bin','HOME':'/tmp','PYTHONPATH':'/home/agent/.local/lib/python3.12/site-packages','LS_CPU_THREADS':'4','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4','HF_HUB_OFFLINE':'1','LANG':'C.UTF-8'}
for key in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','NO_PROXY','http_proxy','https_proxy','all_proxy','no_proxy','SSL_CERT_FILE','SSL_CERT_DIR','REQUESTS_CA_BUNDLE','CURL_CA_BUNDLE']:
 if key in os.environ:env[key]=os.environ[key]
os.chdir(ROOT);os.execve(sys.executable,[sys.executable,*sys.argv[1:]],env)
