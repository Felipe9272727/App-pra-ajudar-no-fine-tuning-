"""Unforced real Rust model -> actual tools -> verification/final stage."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));HERE=ROOT/'tooluse023'
from tooluse022.tools import parse_call,search_web,safe_text
FINAL='Confira a observação real acima e conclua o pedido original com uma resposta breve. Cite somente URLs retornadas se fez uma busca. Se os dados forem insuficientes, diga isso. Faça outra chamada apenas para corrigir um erro ou obter uma informação que falta; não repita uma chamada já bem-sucedida.'
ROWS=[{'id':'app_py_squares21','question':'Use Python para conferir a soma dos quadrados de 1 até 21 e diga o resultado.','expected':'3311','kind':'python'},{'id':'app_web_mathsqrt','question':'Pesquise na web a documentação de math.sqrt do Python e cite uma fonte retornada.','kind':'web'}]
def main():
 path=HERE/'reports/native_app_smoke_fstrings.json';results=json.loads(path.read_text()) if path.exists() else [];scratch=Path('/dev/shm/liquid-android/tools023-smoke');scratch.mkdir(exist_ok=True);clean={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','RAYON_NUM_THREADS':'4'}
 for row in ROWS:
  if any(r['id']==row['id'] for r in results):continue
  messages=[{'role':'user','content':row['question']}];turns=[];started=time.monotonic()
  for step in range(3):
   inp=scratch/'messages.json';inp.write_text(json.dumps(messages,ensure_ascii=False));r=subprocess.run(['/dev/shm/liquid-android/prebuilt/tools023/toolcheck','parent',str(inp)],capture_output=True,text=True,cwd=ROOT,env=clean,timeout=1200);assert r.returncode==0,r.stderr[-1000:];answer=json.loads(r.stdout);raw=answer['raw_text'];t={'step':step,'answer':answer};turns.append(t)
   try:call=parse_call(raw)
   except Exception as e:t['parse_error']=str(e);break
   t['call']=call
   if call is None:break
   if step==2:t['error']='call limit';break
   if call['name']=='search_web':obs=search_web(call['arguments']['query'])
   else:
    try:
     p=subprocess.run(['/dev/shm/liquid-android/tools022/python-host/liquid-python'],input=call['arguments']['code'],capture_output=True,text=True,env=clean,cwd='/tmp',timeout=6);obs={'tool':'run_python','ok':p.returncode==0,'stdout':p.stdout if p.returncode==0 else '', 'runtime':'MicroPython1.26.1 subset, actual C host executable','filesystem':False,'network':False}
     if p.returncode:obs['error']=p.stdout+p.stderr
    except subprocess.TimeoutExpired:obs={'tool':'run_python','ok':False,'error':'watchdog timeout'}
   t['observation']=obs;messages.extend([{'role':'assistant','content':raw},{'role':'tool','content':safe_text(json.dumps(obs,ensure_ascii=False,separators=(',',':')),12000)},{'role':'user','content':FINAL}]);print('APP_TOOL',row['id'],call['name'],obs.get('ok'),flush=True)
  final=turns[-1]['answer']['text'] if not turns[-1].get('call') else '';actual=[t for t in turns if t.get('observation')];ok=bool(final) and any(t['observation'].get('ok') for t in actual)
  if row['kind']=='python':ok=ok and row['expected'] in final and any(row['expected'] in t['observation'].get('stdout','') for t in actual)
  else:ok=ok and any(i['url'] in final for t in actual for i in t['observation'].get('items',[]))
  results.append({'id':row['id'],'question':row['question'],'turns':turns,'correct_with_actual_tool':bool(ok),'seconds_descriptive_only':time.monotonic()-started,'scope':'RustLinux actual model+MicroPythonC; app final control; no Android execution','no_reference_answer_in_input':True});tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');tmp.replace(path);print('APP_SMOKE',row['id'],ok,flush=True)
if __name__=='__main__':main()
