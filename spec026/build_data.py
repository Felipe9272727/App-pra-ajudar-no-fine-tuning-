"""Teaching inputs plus new frozen quality/speed probes; no model outputs used here."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from local_cpu.sandbox import evaluate
H=ROOT/'spec026';D=H/'data';D.mkdir(exist_ok=True)
def save(n,m):
 p=D/n;assert not p.exists();p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
train=json.load(open(ROOT/'review013/train.json'));general=json.load(open(ROOT/'balanced016/general_train.json'));correct=[{'id':r['id'],'prompt':r['prompt'],'answer':r['solution'],'source':'review013_verified_train'} for r in train]+[{'id':r['id'],'prompt':r['prompt'],'answer':r['solution'],'source':'balanced016_general_train'} for r in general]
for i in range(32):
 a=2+i%8;b=3+i//8;correct.append({'id':'S026M/'+str(i),'prompt':f'Responda somente com o número: {a} vezes {b}.','answer':str(a*b),'source':'constructed_checked_math_training'})
save('correct_train.json',correct)
qs=[f'Write a Python function f(x) returning x plus {n}. Return only code.' for n in range(3,11)]+[f'Responda brevemente: quanto é {n} vezes 7?' for n in range(3,11)]+['Explique brevemente o que é uma lista em Python.','What does a Python for loop do? Keep it short.','Como verificar se um número é par em Python?','Explain what a Python dictionary stores, briefly.','What is the difference between a list and a tuple? Briefly.','Explique em uma frase o que é uma variável.','Give a short Python example that prints a greeting.','Why test empty input when writing a function? Briefly.']
save('teacher_prompts.json',[{'id':f'S026D/{i:02d}','prompt':q} for i,q in enumerate(qs)])
def row(id,prompt,solution,inputs,oracle):
 r={'id':id,'prompt':prompt+' Return only the function, without imports or explanations.','solution':solution,'cases':[{'args':[x],'expected':oracle(x)} for x in inputs]};a=evaluate(solution,r);assert a['all_passed'],(id,a);assert not evaluate('def solve(x): return None',r)['all_passed'];return r
quality=[]
quality.append(row('S026Q/reverse_words','Write Python function solve(s). Split on whitespace and return the words in reverse order joined by one space.','def solve(s):\n    return " ".join(s.split()[::-1])',['','a','a b','one two three','  a   b  '],lambda s:' '.join(s.split()[::-1])))
quality.append(row('S026Q/absolute_sum','Write Python function solve(xs). Return the sum of absolute values of all integers in xs.','def solve(xs):\n    return sum(abs(x) for x in xs)\n',[[],[0],[-5],[1,-2,3],[-4,-4]],lambda xs:sum(map(abs,xs))))
quality.append(row('S026Q/equal_pairs','Write Python function solve(xs). Count index pairs i<j whose values are equal. Return an integer.','def solve(xs):\n    return sum(xs[i]==xs[j] for i in range(len(xs)) for j in range(i+1,len(xs)))\n',[[],[1],[1,1],[1,1,1],[1,2,1,2],[0,0,0,0]],lambda x:sum(x[i]==x[j] for i in range(len(x)) for j in range(i+1,len(x)))))
quality.append(row('S026Q/second','Write Python function solve(xs). Return the second largest distinct integer. Return None when fewer than two distinct values exist.','def solve(xs):\n    ys=sorted(set(xs))\n    return ys[-2] if len(ys)>1 else None\n',[[],[1],[2,2],[1,3,2],[5,5,-2,3],[-4,-1,-2]],lambda x:sorted(set(x))[-2] if len(set(x))>=2 else None))
quality.append(row('S026Q/flatten','Write Python function solve(rows). Flatten a list of lists by one level, preserving item order.','def solve(rows):\n    return [x for row in rows for x in row]\n',[[],[[]],[[1]],[[1,2],[],[3]],[[0],[-1,-2]]],lambda rows:sum(rows,[])))
def prod(xs):
 out=[];v=1
 for x in xs:v*=x;out.append(v)
 return out
quality.append(row('S026Q/products','Write Python function solve(xs). Return the inclusive cumulative products, starting with multiplicative identity 1.','def solve(xs):\n    out=[]\n    v=1\n    for x in xs:\n        v*=x\n        out.append(v)\n    return out\n',[[],[2],[2,3,4],[2,0,4],[-2,-3,1]],prod))
quality.append(row('S026Q/palindrome','Write Python function solve(s). Ignore nonletters and case, and return whether the resulting letters form a palindrome.','def solve(s):\n    s="".join(c.lower() for c in s if c.isalpha())\n    return s==s[::-1]\n',['','A','abba','abc','A man, a plan, a canal: Panama!','12'],lambda s:(lambda t:t==t[::-1])(''.join(c.lower() for c in s if c.isalpha()))))
def interleave(pair):
 a,b=pair;out=[]
 for i in range(max(len(a),len(b))):
  if i<len(a):out.append(a[i])
  if i<len(b):out.append(b[i])
 return out
quality.append(row('S026Q/interleave','Write Python function solve(pair). pair contains lists a and b. Interleave a[0],b[0],a[1],b[1],... and append any remaining tail.','def solve(pair):\n    a,b=pair\n    out=[]\n    for i in range(max(len(a),len(b))):\n        if i<len(a):out.append(a[i])\n        if i<len(b):out.append(b[i])\n    return out\n',[[[],[]],[[1],[]],[[],[2]],[[1,2],[3,4]],[[1],[2,3,4]]],interleave))
save('quality_code.json',quality)
qg=[('Responda somente com o número: 13 vezes 7.','91',True),('Reply only with a number: 29 minus 12.','17',True),('Iara chegou antes de João. João chegou antes de Lia. Quem chegou primeiro? Responda somente o nome.','Iara',False),('Give only the plural of child.','children',False),('What is the capital of France? Reply only with the city.','Paris',False),('Traduza red para português. Responda uma palavra.','vermelho',False),('Responda apenas: SIM','SIM',False),('Todo mamífero é um animal. Uma foca é mamífero. A foca é um animal? Responda apenas sim ou não.','sim',False)]
save('quality_general.json',[{'id':f'S026G/{i}','question':q,'answer':a,'numeric':n,'aliases':[]} for i,(q,a,n) in enumerate(qg)])
speed=['Write a Python function triple(x) that returns x multiplied by three. Return only code.','Explique brevemente por que testar entradas vazias em uma função.','List three properties of a Python dictionary, briefly.','Write Python function square(x), returning x*x. Return only code.','Qual é a diferença entre uma lista e uma tupla? Resuma.','Write a short Python function that returns the largest value of a nonempty list.','Explique em duas frases o que faz um laço for.','Give two simple ways to check a Python function result.']
save('speed_prompts.json',[{'id':f'S026S/{i}','prompt':q} for i,q in enumerate(speed)])
assert len(set(r['prompt'] for r in correct))==len(correct)
train_strings={r['prompt'] for r in correct}|set(qs);assert all(r['prompt'] not in train_strings for r in quality);assert not set(speed)&train_strings
save('construction_audit.json',{'correct_training_samples':len(correct),'teacher_prompts':24,'quality_code':8,'quality_general':8,'speed_prompts':8,'quality_reference_cases':sum(len(r['cases']) for r in quality),'all_quality_references_passed':True,'all_None_mutants_rejected':True,'quality_speed_exact_prompts_excluded_from_training':True,'ordinary_skill_and_pretraining_overlap_possible':True,'prior025_final_not_read':True})
print('DATA_CONSTRUCTION_COMPLETE')
