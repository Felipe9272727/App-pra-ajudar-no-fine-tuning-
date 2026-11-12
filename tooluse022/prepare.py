"""Freeze teacher traces with actual tool observations and four unseen tasks."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tooluse022.tools import SCHEMAS,SYSTEM,execute,call_text
HERE=ROOT/'tooluse022'
def main():
 assert not (HERE/'train.json').exists(),'Do not replace observed/frozen data'
 py=[
 ('py01','Use Python para calcular a soma dos quadrados de 1 até 17. Confira o cálculo e responda o resultado.','n=17\ns=sum(i*i for i in range(1,n+1))\nassert s==n*(n+1)*(2*n+1)//6\nprint(s)'),
 ('py02','Execute Python para calcular o MDC de 462 e 1071. Confira a divisibilidade e responda.','import math\na,b=462,1071\ng=math.gcd(a,b)\nassert a%g==0 and b%g==0\nprint(g)'),
 ('py03','Confira em Python o total acumulado da lista [7,-2,9,4] e responda os quatro totais.','xs=[7,-2,9,4]\nout=[]\ns=0\nfor x in xs:\n s+=x\n out.append(s)\nassert out[-1]==sum(xs)\nprint(out)'),
 ('py04','Use Python para achar a raiz inteira de 123456789. Confira os limites ao quadrado.','import math\nn=123456789\nr=math.isqrt(n)\nassert r*r<=n<(r+1)*(r+1)\nprint(r)'),
 ]
 web=[
 ('web01','Busque na internet a documentação de json.dumps do Python e cite uma fonte encontrada.','Python json dumps official documentation'),
 ('web02','Pesquise na web a documentação de String em Rust. Cite uma fonte retornada.','Rust String official documentation'),
 ('web03','Busque na web a documentação de listas em Kotlin e cite uma fonte encontrada.','Kotlin lists official documentation'),
 ('web04','Pesquise a documentação do módulo math no MicroPython e cite uma fonte retornada.','MicroPython math official documentation'),
 ]
 progress=HERE/'collection.json';rows=json.loads(progress.read_text()) if progress.exists() else []
 for kind,items in [('python',py),('web',web)]:
  for ident,question,arg in items:
   if any(r['id']==ident+'_final' for r in rows):continue
   name,key=('run_python','code') if kind=='python' else ('search_web','query');call={'name':name,'arguments':{key:arg}};observation=execute(call);assert observation['ok'],observation
   plan='Vou executar e verificar o cálculo.' if kind=='python' else 'Vou buscar uma fonte e conferir os resultados.'
   assistant=plan+'\n'+call_text(name,key,arg)
   if kind=='python':final='Conferi a execução e a verificação passou. Resultado: '+observation['stdout'].strip()+'.'
   else:
    item=observation['items'][0];final='A busca retornou '+item['title']+'. Fonte: '+item['url']
   messages=[{'role':'system','content':SYSTEM},{'role':'user','content':question}]
   rows.append({'id':ident,'kind':kind,'messages':messages,'target':assistant,'teaching_only':True})
   rows.append({'id':ident+'_final','kind':kind,'messages':messages+[{'role':'assistant','content':assistant},{'role':'tool','content':json.dumps(observation,ensure_ascii=False,separators=(',',':'))}],'target':final,'teaching_only':True})
   tmp=progress.with_suffix('.tmp');tmp.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');tmp.replace(progress)
   print('PREPARED_ACTUAL_TEACHING',ident,flush=True)
 # Input numbers and lookup subjects differ from all teaching traces.
 fresh=[{'id':'fresh_py01','kind':'python','question':'Execute Python para calcular a soma dos cubos de 1 até 23. Confira e responda o número.','expected':'76176'},
 {'id':'fresh_py02','kind':'python','question':'Use Python para calcular o MMC de 84 e 198. Verifique e diga o resultado.','expected':'2772'},
 {'id':'fresh_web01','kind':'web','question':'Busque na web a documentação de heapq.heappush do Python e cite uma fonte retornada.','query_terms':['heapq','heappush']},
 {'id':'fresh_web02','kind':'web','question':'Pesquise na internet a documentação de Vec::push em Rust e cite uma fonte encontrada.','query_terms':['vec','push']}]
 (HERE/'train.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');(HERE/'fresh.json').write_text(json.dumps(fresh,ensure_ascii=False,indent=2)+'\n');(HERE/'tool_config.json').write_text(json.dumps({'system':SYSTEM,'schemas':SCHEMAS},ensure_ascii=False,indent=2)+'\n')
 paths=['tooluse022/PROTOCOL.md','tooluse022/tools.py','tooluse022/prepare.py','tooluse022/train.json','tooluse022/fresh.json','tooluse022/tool_config.json']
 (HERE/'data_frozen.json').write_text(json.dumps({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
if __name__=='__main__':main()
