"""Fresh029 validation only; teaching is unchanged and old final stays sealed."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from local_cpu.sandbox import evaluate
H=ROOT/'native029'

def main():
 tasks=[]
 def add(name,description,solution,args,expected):
  row={'id':'N029V/'+name,'family':name,'prompt':'Write Python function solve. '+description+' Return only the complete function after any thinking. Do not import modules.',
   'solution':solution,'cases':[{'args':a,'expected':e} for a,e in zip(args,expected)]}
  assert evaluate(solution,row)['all_passed'],name
  assert not evaluate('def solve(*args): return None',row)['all_passed'];tasks.append(row)
 add('chunks','Given a list xs and integer k>0, split xs into consecutive lists of length k; include the shorter last chunk. Empty input gives [].',
  'def solve(xs,k):\n    return [xs[i:i+k] for i in range(0,len(xs),k)]',
  [[[],2],[[1,2,3,4,5],2],[[1,2],3],[[7,8],1],[[0,0,0,0],2]],
  [[],[[1,2],[3,4],[5]],[[1,2]],[[7],[8]],[[0,0],[0,0]]])
 add('anagram_groups','Given list words of lowercase ASCII strings, group anagrams. Preserve word order within each group and order groups by first occurrence of a member. Repeated words stay repeated. Return list of lists.',
  'def solve(words):\n    groups={}\n    for word in words:\n        key="".join(sorted(word))\n        groups.setdefault(key,[]).append(word)\n    return list(groups.values())',
  [[[]],[['eat','tea','tan','ate','nat','bat']],[['','a','']],[['ab','ba','ab']],[['cat','dog']]],
  [[],[['eat','tea','ate'],['tan','nat'],['bat']],[['',''],['a']],[['ab','ba','ab']],[['cat'],['dog']]])
 add('sliding_max','Given integer list xs and integer k>0, return the maximum of every consecutive window of exactly k elements. Return [] if no full window exists.',
  'def solve(xs,k):\n    return [max(xs[i:i+k]) for i in range(len(xs)-k+1)]',
  [[[],1],[[1,3,-1,-3,5,3,6,7],3],[[-4,-2,-5],2],[[2,2],1],[[1,2],3]],
  [[],[3,3,5,5,6,7],[-2,-2],[2,2],[]])
 add('components','Given n>=0 and list edges of undirected edges [u,v], vertices are 0..n-1. Return the number of connected components, counting isolated vertices. Self-edges and repeated edges are allowed.',
  'def solve(n,edges):\n    graph=[[] for j in range(n)]\n    for a,b in edges:\n        graph[a].append(b)\n        graph[b].append(a)\n    seen=set()\n    count=0\n    for v in range(n):\n        if v in seen: continue\n        count+=1\n        stack=[v]\n        seen.add(v)\n        while stack:\n            x=stack.pop()\n            for y in graph[x]:\n                if y not in seen:\n                    seen.add(y)\n                    stack.append(y)\n    return count',
  [[0,[]],[3,[]],[5,[[0,1],[1,2],[3,4]]],[3,[[0,1],[1,2],[2,0]]],[3,[[0,0],[0,1],[0,1]]]],
  [0,3,2,1,2])
 general=[]
 def gen(i,prompt,answers):general.append({'id':f'N029G/{i}','prompt':prompt,'answers':answers})
 gen(0,'Responda somente com o número: 19 vezes 7.',['133'])
 gen(1,'Reply only with the integer remainder: 59 divided by 8.',['3'])
 gen(2,'Ana arrived before Bia. Bia arrived before Caio. Who arrived first? Reply with the name only.',['Ana'])
 gen(3,'Dê somente o plural de pão.',['pães'])
 gen(4,'Traduza yellow para português. Responda uma palavra.',['amarelo'])
 gen(5,'What is the capital of Norway? Reply only with the city.',['Oslo'])
 gen(6,'Toda ave é um animal. Uma coruja é uma ave. Uma coruja é um animal? Responda apenas sim ou não.',['sim'])
 gen(7,'Qual é mutável em Python: lista ou tupla? Responda uma palavra.',['lista','list'])
 for file,rows in [('validation_code.json',tasks),('validation_general.json',general)]:
  p=H/'data'/file;assert not p.exists();p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
 training=[]
 for file in ['train_code.json','train_general.json','anchors.json']:
  training.extend(json.load(open(H/'data'/file)))
 assert not ({x['prompt'] for x in tasks+general}&{x['prompt'] for x in training})
 (H/'reports/validation_construction.json').write_text(json.dumps({'fresh_code_families':4,'cases':20,'general':8,'references_pass_real_sandbox':True,'null_mutants_rejected':True,'no_project_model_inference_performed':True,'old028_final_remains_unqueried_and_reused_only_as_reserved_final':True},indent=2)+'\n')
 print('NEW029_VALIDATION_VERIFIED4_20_8_NO_MODEL_OUTPUTS')
if __name__=='__main__':main()
