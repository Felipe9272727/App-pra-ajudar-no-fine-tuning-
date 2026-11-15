"""Wrap the exact archived APK; verify local/archive/remote bytes without rebuilding."""
from pathlib import Path
import argparse,hashlib,json,zipfile
APK_NAME='LiquidSense-0.6.3-install-preview.apk'
APK_SHA='4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10'
APK_BYTES=1967560403
ZIP_NAME='LiquidSense-0.6.3-verificado.zip'
REPO='Felipe9272727/App-pra-ajudar-no-fine-tuning-'
TAG='liquid-sense-0.6.3-verified035'
def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def wrapped_check(path):
 with zipfile.ZipFile(path) as z:
  assert set(z.namelist())=={APK_NAME,'LEIA-ME.txt'},z.namelist()
  i=z.getinfo(APK_NAME);assert i.file_size==APK_BYTES
  with z.open(i) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==APK_SHA
  assert z.testzip() is None

def main():
 p=argparse.ArgumentParser();p.add_argument('--apk',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--remote',type=Path);p.add_argument('--stage',choices=['authenticated_draft','public_anonymous']);a=p.parse_args();a.out.mkdir(exist_ok=True)
 mpath=a.out/'delivery_manifest.json'
 if a.remote:
  m=json.loads(mpath.read_text());assert a.remote.stat().st_size==m['zip']['bytes'];assert sha(a.remote)==m['zip']['sha256'];wrapped_check(a.remote);m.setdefault('verified_remote_stages',[]).append(a.stage);m['full_public_redownload_verified']='public_anonymous'in m['verified_remote_stages'];mpath.write_text(json.dumps(m,indent=2)+'\n');print('REMOTE_ZIP_AND_CONTAINED_APK_VERIFIED',a.stage,flush=True);return
 assert a.apk and a.apk.stat().st_size==APK_BYTES and sha(a.apk)==APK_SHA
 archive=a.out/ZIP_NAME;assert not archive.exists()
 with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_STORED) as z:
  z.write(a.apk,APK_NAME)
  z.writestr('LEIA-ME.txt','''Liquid Sense 0.6.3 — mesma versão, entrega com integridade verificável.

1. Extraia este ZIP no gerenciador de arquivos do celular.
2. Abra o APK extraído para instalar. Não desinstale o app antigo.
3. Se houver recusa, use o Liquid Sense · Verificador que você já instalou:
   escolha o APK extraído, aguarde a conferência e use o botão 2 se liberado.
   Depois copie o relatório e envie na conversa.

APK: 1967560403 bytes
SHA256: 4735be854079941188e5f918e82d7c21d5468a437efe1bf7f45e72c15ade0e10

O ZIP adiciona verificação de corrupção ao transporte, não muda os pesos,
a assinatura ou o app. A instalação no seu Xiaomi ainda precisa ser confirmada.
A Base continua padrão. A época2 é experimental e não provou ganho geral.
''')
 wrapped_check(archive)
 m={'purpose':'same_exact_signed_APK_with_new_delivery_transport','apk':{'name':APK_NAME,'bytes':APK_BYTES,'sha256':APK_SHA},'zip':{'name':ZIP_NAME,'bytes':archive.stat().st_size,'sha256':sha(archive)},'url':f'https://github.com/{REPO}/releases/download/{TAG}/{ZIP_NAME}','archive_source_commit':'04990ad71bbc9a03829e6b31759a2297692aab3e','full_public_redownload_verified':False,'physical_installation_verified':False,'model_weights_changed':False}
 mpath.write_text(json.dumps(m,indent=2)+'\n');(a.out/'SHA256SUMS.txt').write_text(m['zip']['sha256']+'  '+ZIP_NAME+'\n'+APK_SHA+'  '+APK_NAME+'\n');print(json.dumps(m),flush=True)
if __name__=='__main__':main()
