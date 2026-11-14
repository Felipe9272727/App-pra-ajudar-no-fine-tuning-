"""New fixed teaching and reserved tasks; references checked in the existing sandbox."""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from local_cpu.sandbox import evaluate
from tooluse022.tools import run_python
H = ROOT / 'native028'
D = H / 'data'


def save(name, obj):
    p = D / name
    assert not p.exists(), 'Do not overwrite frozen data'
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def task(name, description, code, inputs, oracle, plan, buggy=None):
    prompt = 'Write Python function solve. ' + description
    if buggy:
        prompt += '\nRepair this incorrect implementation:\n' + buggy
    prompt += '\nReturn only the complete function after any thinking. Do not import modules.'
    row = {'id': name, 'family': name.split('/')[-1], 'prompt': prompt,
           'solution': code, 'plan': plan,
           'cases': [{'args': args, 'expected': oracle(*args)} for args in inputs]}
    check = evaluate(code, row)
    assert check['all_passed'], (name, check)
    assert not evaluate('def solve(*args): return None', row)['all_passed']
    return row


def main():
    D.mkdir(exist_ok=True)
    T = []
    def add(*args, **kw):
        T.append(task('N028T/' + args[0], *args[1:], **kw))
    add('inclusive_sum', 'Given integer n>=0, sum all integers from 1 through n, inclusive.',
        'def solve(n):\n    return n*(n+1)//2', [[0],[1],[2],[8],[15]], lambda n:n*(n+1)//2,
        'The upper endpoint is inclusive. The arithmetic-series formula also gives zero for n=0.',
        buggy='def solve(n): return sum(range(n))')
    add('squares', 'Given a list xs of integers, return their squares in the same order.',
        'def solve(xs):\n    return [x*x for x in xs]', [[[]],[[0]],[[-2,3]],[[5,-1,4]]], lambda xs:list(map(lambda x:x*x,xs)),
        'Transform each element independently and preserve order; an empty list stays empty.')
    add('multiples_three', 'Return only integers in xs divisible by 3, preserving order.',
        'def solve(xs):\n    return [x for x in xs if x%3==0]', [[[]],[[1,2]],[[-3,0,4,6]],[[9,9,10]]], lambda xs:list(filter(lambda x:x%3==0,xs)),
        'A remainder of zero selects multiples, including zero and negative multiples.')
    add('trim_words', 'Given a list of strings xs, strip whitespace from each string.',
        'def solve(xs):\n    return [x.strip() for x in xs]', [[[]],[[' a ','b\n']],[[' ',' c']]], lambda xs:list(map(str.strip,xs)),
        'Strip each string separately; preserve the number and order of items.')
    add('vowels', 'Count ASCII vowels in string s, ignoring case.',
        'def solve(s):\n    return sum(c.lower() in "aeiou" for c in s)', [[''],['AEi'],['sky'],['hello world']], lambda s:sum(s.lower().count(c) for c in 'aeiou'),
        'Normalize case and count only a,e,i,o,u. Non-vowels add zero.')
    add('digit_sum', 'Return the sum of decimal digits of integer n; ignore its sign.',
        'def solve(n):\n    return sum(int(c) for c in str(abs(n)))', [[0],[109],[-583],[7007]], lambda n:sum(map(int,str(abs(n)))),
        'Remove the sign before reading digits. Zero has digit sum zero.')
    add('factorial', 'Given integer n>=0, return n factorial.',
        'def solve(n):\n    out=1\n    for k in range(2,n+1):\n        out*=k\n    return out', [[0],[1],[3],[6]], math.factorial,
        'Start the product at one so the empty product for zero is correct.',
        buggy='def solve(n):\n    out=0\n    for k in range(1,n+1): out*=k\n    return out')
    add('gcd', 'Given integers a and b, return their nonnegative greatest common divisor; gcd(0,0)=0.',
        'def solve(a,b):\n    a,b=abs(a),abs(b)\n    while b:\n        a,b=b,a%b\n    return a', [[0,0],[12,18],[-15,5],[7,0],[17,13]], math.gcd,
        'Use Euclid on absolute values. The zero cases follow from stopping when b is zero.')
    add('prime', 'Return whether integer n is prime. Integers below 2 are not prime.',
        'def solve(n):\n    if n<2: return False\n    d=2\n    while d*d<=n:\n        if n%d==0: return False\n        d+=1\n    return True', [[0],[1],[2],[9],[17],[25]], lambda n:n>=2 and all(n%d for d in range(2,n)),
        'Reject numbers below two first. Test divisors through the square root, including perfect squares.',
        buggy='def solve(n): return all(n%d for d in range(2,n))')
    add('move_last', 'For string s, move its last character to the front. Empty stays empty.',
        'def solve(s):\n    return s[-1:]+s[:-1]', [[''],['a'],['abcd'],['xy']], lambda s:s[-1]+s[:-1] if s else '',
        'Slices handle an empty string safely; concatenate the last-character slice and the rest.')
    add('nonempty', 'Filter out exactly the empty strings from xs; preserve spaces and order.',
        'def solve(xs):\n    return [x for x in xs if x!=""]', [[[]],[['','a',' ','']],[['b','c']]], lambda xs:list(filter(lambda x:len(x)>0,xs)),
        'Only length-zero strings are excluded. A string containing spaces is retained.')
    add('span', 'Return max(xs)-min(xs) for integer list xs, or 0 when empty.',
        'def solve(xs):\n    return max(xs)-min(xs) if xs else 0', [[[]],[[2]],[[4,-3,8]],[[-2,-1]]], lambda xs:sorted(xs)[-1]-sorted(xs)[0] if xs else 0,
        'Handle the empty list before taking extrema. A single value has span zero.')
    add('stable_unique', 'Return distinct items of xs in first-occurrence order.',
        'def solve(xs):\n    seen=set()\n    out=[]\n    for x in xs:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out', [[[]],[[1,1,2,1,3]],[[0,0]],[['a','b','a']]], lambda xs:list(dict.fromkeys(xs)),
        'Use a membership set but append on first occurrence; a sorted set would lose input order.')
    add('sign_counts', 'Return [positive_count, negative_count] for xs; ignore zeros.',
        'def solve(xs):\n    return [sum(x>0 for x in xs),sum(x<0 for x in xs)]', [[[]],[[0,1,-2,3,0]],[[0,0]],[[-1,-2]]], lambda xs:[len([x for x in xs if x>0]),len([x for x in xs if x<0])],
        'Use strict comparisons so zeros enter neither count.')
    add('prefix_sum', 'Return inclusive running sums of integer list xs.',
        'def solve(xs):\n    out=[]\n    total=0\n    for x in xs:\n        total+=x\n        out.append(total)\n    return out', [[[]],[[0]],[[1,2,3]],[[-1,4,-2]]], lambda xs:[sum(xs[:i+1]) for i in range(len(xs))],
        'Initialize the running total to zero, then add before appending.',
        buggy='def solve(xs):\n    out=[]\n    total=1\n    for x in xs:\n        total+=x\n        out.append(total)\n    return out')
    add('differences', 'Return consecutive differences xs[i+1]-xs[i]. Lists shorter than two give [].',
        'def solve(xs):\n    return [xs[i+1]-xs[i] for i in range(len(xs)-1)]', [[[]],[[7]],[[2,5,1]],[[-2,0,3]]], lambda xs:[b-a for a,b in zip(xs,xs[1:])],
        'Subtract the earlier value from the later one. Empty and singleton inputs have no adjacent pairs.',
        buggy='def solve(xs): return [xs[i]-xs[i+1] for i in range(len(xs)-1)]')
    add('clamp', 'Given xs, low and high with low<=high, clamp every value into [low,high].',
        'def solve(xs,low,high):\n    return [max(low,min(high,x)) for x in xs]', [[[],0,3],[[-2,1,6],0,4],[[1,1],2,2]], lambda xs,low,high:[low if x<low else high if x>high else x for x in xs],
        'Apply the lower and upper bounds to each item. Equal bounds produce a constant list.')
    add('sort_odds', 'Sort all odd integers in xs into ascending order; return only the odd integers.',
        'def solve(xs):\n    return sorted(x for x in xs if x%2!=0)', [[[]],[[4,1,3,2,-5]],[[2,8]],[[1,1]]], lambda xs:sorted(filter(lambda x:x%2,xs)),
        'Filter odd numbers before sorting. Negative odd numbers also have a nonzero remainder.')
    add('square_dictionary', 'Return a dictionary mapping str(x) to x*x for the integers in xs.',
        'def solve(xs):\n    return {str(x):x*x for x in xs}', [[[]],[[2,-3,2]],[[0,1]]], lambda xs:dict((str(x),pow(x,2)) for x in xs),
        'Dictionary keys are strings as requested; duplicate integers overwrite with the same square.')
    add('character_counts', 'Return a character-frequency dictionary for string s, case-sensitive.',
        'def solve(s):\n    counts={}\n    for c in s:\n        counts[c]=counts.get(c,0)+1\n    return counts', [[''],['aba'],['Aa A'],['1112']], lambda s:{c:s.count(c) for c in set(s)},
        'Count each character exactly, including spaces and case differences.')
    add('word_lengths', 'Split s on whitespace and return the length of each word.',
        'def solve(s):\n    return [len(w) for w in s.split()]', [[''],['  hi  there '],['a bc def'],['x\ny']], lambda s:list(map(len,s.split())),
        'Whitespace splitting removes empty pieces; preserve the resulting word order.')
    def collatz(n):
        steps=0
        while n!=1:
            n=n//2 if n%2==0 else 3*n+1
            steps+=1
        return steps
    add('collatz_steps', 'For positive integer n, count Collatz transformations until reaching 1.',
        'def solve(n):\n    steps=0\n    while n!=1:\n        n=n//2 if n%2==0 else 3*n+1\n        steps+=1\n    return steps', [[1],[2],[3],[7],[10]], collatz,
        'Count transformations, not visited values. Starting at one requires zero transformations.')
    add('power_two', 'Return whether integer n is a positive power of two.',
        'def solve(n):\n    return n>0 and (n&(n-1))==0', [[-2],[0],[1],[2],[3],[16]], lambda n:n>0 and bin(n).count('1')==1,
        'A positive power of two has one set bit. Positivity excludes zero and negatives.')
    add('triangle', 'Given lengths a,b,c, return whether they form a nondegenerate triangle.',
        'def solve(a,b,c):\n    return min(a,b,c)>0 and a+b>c and a+c>b and b+c>a', [[3,4,5],[1,2,3],[0,1,1],[-1,3,3],[2,2,2]], lambda a,b,c:min(a,b,c)>0 and sum([a,b,c])-max(a,b,c)>max(a,b,c),
        'Require positive sides and strict triangle inequalities. Equality is a degenerate line.',
        buggy='def solve(a,b,c): return a+b>=c and a+c>=b and b+c>=a')
    add('alternating_sum', 'Return xs[0]-xs[1]+xs[2]-... for integer list xs.',
        'def solve(xs):\n    return sum(x if i%2==0 else -x for i,x in enumerate(xs))', [[[]],[[3]],[[1,2,3,4]],[[-1,-2,-3]]], lambda xs:sum(xs[::2])-sum(xs[1::2]),
        'Even indices contribute positively and odd indices negatively. Empty gives zero.')
    add('all_distinct', 'Return whether all items of xs are distinct.',
        'def solve(xs):\n    return len(set(xs))==len(xs)', [[[]],[[1]],[[1,2,1]],[['a','b']]], lambda xs:all(xs.count(x)==1 for x in xs),
        'Compare set size with list size. Empty and singleton lists are distinct.')
    add('reverse_word_letters', 'Reverse the letters within each whitespace-separated word of s; join with single spaces.',
        'def solve(s):\n    return " ".join(w[::-1] for w in s.split())', [[''],['ab cd'],['  hello  a ']], lambda s:' '.join(''.join(reversed(w)) for w in s.split()),
        'Reverse each word separately without reversing word order; normalize separating spaces.')
    add('negative_index', 'Return the index of the first negative value in xs, or -1 if absent.',
        'def solve(xs):\n    for i,x in enumerate(xs):\n        if x<0: return i\n    return -1', [[[]],[[0,2]],[[1,-2,-3]],[[-1,0]]], lambda xs:next((i for i,x in enumerate(xs) if x<0),-1),
        'The comparison must be negative, and return immediately for the first match.',
        buggy='def solve(xs):\n    for i,x in enumerate(xs):\n        if x>0: return i\n    return -1')
    add('repeat_pattern', 'Given string s and nonnegative n, return s repeated n times.',
        'def solve(s,n):\n    return s*n', [['ab',0],['x',3],['',5],['ha',2]], lambda s,n:''.join([s for _ in range(n)]),
        'String multiplication preserves the pattern. Zero repetitions and empty patterns give empty strings.')
    add('threshold_keys', 'Given dictionary d of string keys and numeric values, return sorted keys with value strictly above k.',
        'def solve(d,k):\n    return sorted(key for key,value in d.items() if value>k)', [[{},2],[{'a':2,'b':3,'c':1},2],[{'x':-1,'z':0},-1]], lambda d,k:sorted(filter(lambda key:d[key]>k,d)),
        'Use a strict threshold and sort the selected keys; equal values are excluded.',
        buggy='def solve(d,k): return sorted(key for key,value in d.items() if value>=k)')
    add('merge_counts', 'Given dictionaries a,b with string keys and integer counts, sum counts for each key in their union.',
        'def solve(a,b):\n    out=a.copy()\n    for key,value in b.items():\n        out[key]=out.get(key,0)+value\n    return out', [[{},{}],[{'x':2},{'x':3,'y':1}],[{'a':-2},{'b':0}]], lambda a,b:{k:a.get(k,0)+b.get(k,0) for k in set(a)|set(b)},
        'Start from a copy, add the second dictionary, and treat missing counts as zero.')
    add('substring_count', 'Count occurrences of nonempty substring sub in s, including overlaps.',
        'def solve(s,sub):\n    return sum(s[i:i+len(sub)]==sub for i in range(len(s)-len(sub)+1))', [['','a'],['aaa','aa'],['ababa','aba'],['abc','x'],['abc','abcd']], lambda s,sub:sum(s.startswith(sub,i) for i in range(len(s))),
        'Try every start position so overlapping matches count; do not advance by the whole substring.')
    assert len(T)==32
    general = [
        ('Responda somente com o número: 14 vezes 6.','84','Multiplicar quatorze por seis fornece o produto solicitado.'),
        ('Reply only with the integer: 91 minus 38.','53','Subtract the two integers and return the result.'),
        ('Qual é a capital de Portugal? Responda apenas o nome.','Lisboa','A capital de Portugal é Lisboa.'),
        ('What is the capital of Spain? Reply with the city only.','Madrid','Use the country-capital fact and return the city.'),
        ('Traduza green para português. Responda uma palavra.','verde','A tradução de green neste contexto é verde.'),
        ('Give only the plural of mouse (the animal).','mice','The animal noun has an irregular plural.'),
        ('Ana chegou antes de Bia; Bia chegou antes de Caio. Quem chegou primeiro? Apenas o nome.','Ana','A ordem informada coloca Ana antes de Bia e de Caio.'),
        ('Todo quadrado tem quatro lados. Esta figura é um quadrado. Tem quatro lados? Apenas sim ou não.','sim','Aplicar a propriedade de todos os quadrados à figura dada.'),
        ('Em Python, qual é mutável: list ou tuple? Responda apenas list ou tuple.','list','List permite alterações; tuple não permite alterar seus elementos.'),
        ('What keyword defines a Python function? Reply with one keyword.','def','Python function definitions start with def.'),
        ('Responda exatamente com a palavra: pronto','pronto','Cumprir o formato pedido sem acrescentar explicações.'),
        ('A box has 5 red balls and 7 blue balls. How many balls total? Reply only with a number.','12','Add the two disjoint groups.'),
    ]
    G = [{'id':f'N028G/{i}','prompt':q,'solution':a,'plan':p} for i,(q,a,p) in enumerate(general)]
    schemas = [json.loads((ROOT/'tooluse023/tool_config.json').read_text())['schemas'][1]]
    def call(code):
        return '<tool_call>\n<function=run_python>\n<parameter=code>\n'+code+'\n</parameter>\n</function>\n</tool_call>'
    system='Use run_python for requested calculations. Inspect real tool output before reporting a result. Do not invent executions.'
    code='n=9\ns=sum(i*i*i for i in range(1,n+1))\nassert s==(n*(n+1)//2)**2\nprint(s)'
    obs=run_python(code);assert obs['ok'] and obs['stdout'].strip()=='2025'
    messages=[{'role':'system','content':system},{'role':'user','content':'Use Python to sum the cubes of integers from 1 through 9, check the result, then answer only the number.'}]
    history=messages+[{'role':'assistant','content':call(code)},{'role':'tool','content':json.dumps(obs)}]
    bad=run_python('print(1/0)');assert not bad['ok']
    repair_messages=[{'role':'system','content':system},{'role':'user','content':'Use Python to calculate the average of [2,4,9]. Correct any failed execution and answer only the number.'},{'role':'assistant','content':call('print(1/0)')},{'role':'tool','content':json.dumps(bad)}]
    repaired='xs=[2,4,9]\nprint(sum(xs)/len(xs))';fixed=run_python(repaired);assert fixed['ok'] and fixed['stdout'].strip()=='5.0'
    U=[{'id':'N028U/call','messages':messages,'solution':call(code),'plan':'Call Python and verify the sum before giving a numeric answer.','schemas':schemas},
       {'id':'N028U/final','messages':history,'solution':'2025','plan':'The execution and its assertion succeeded; report the observed number.','schemas':schemas},
       {'id':'N028U/repair','messages':repair_messages,'solution':call(repaired),'plan':'The previous code divided by zero and did not compute the requested average. Recompute from the nonempty input list.','schemas':schemas},
       {'id':'N028U/repaired_final','messages':repair_messages+[{'role':'assistant','content':call(repaired)},{'role':'tool','content':json.dumps(fixed)}],'solution':'5.0','plan':'The corrected execution succeeded; use its observed output.','schemas':schemas}]
    anchors=[('Explique brevemente o que é uma variável em Python.','Uma variável associa um nome a um valor que o programa pode usar.'),
             ('Explain briefly why tests should include empty input.','Empty inputs often exercise boundary cases that ordinary inputs miss.'),
             ('O que uma lista Python armazena? Resuma.','Uma lista armazena uma sequência ordenada de elementos e pode ser modificada.'),
             ('What does a dictionary map in Python?','A dictionary maps keys to values.'),
             ('Qual é a capital da Itália? Responda uma palavra.','Roma'),
             ('What is the capital of Japan? Reply only with the city.','Tokyo'),
             ('Traduza hello para português.','Olá'),
             ('Reply only with a number: 8 plus 11.','19'),
             ('Dê uma dica curta para localizar um erro em código.','Reproduza o problema com um caso pequeno e compare o resultado com o esperado.'),
             ('Explain what a Python return statement does.','It ends the function call and sends a value back to the caller.'),
             ('Qual é o contrário de aumentar? Responda uma palavra.','diminuir'),
             ('Name one reason to use a function in a program.','A function groups reusable behavior behind a clear interface.')]
    A=[{'id':f'N028A/{i}','prompt':q,'solution':a} for i,(q,a) in enumerate(anchors)]
    V=[]
    V.append(task('N028V/transpose','Given rectangular matrix rows, return its transpose as lists. Empty matrix gives [].',
        'def solve(rows):\n    return [list(col) for col in zip(*rows)]', [[[]],[[[]]],[[[1,2],[3,4]]],[[[1],[2],[3]]],[[[1,2,3]]]], lambda rows:[[row[i] for row in rows] for i in range(len(rows[0]))] if rows else [], ''))
    def merge(xs):
        out=[]
        for a,b in sorted(xs):
            if out and a<=out[-1][1]:out[-1][1]=max(out[-1][1],b)
            else:out.append([a,b])
        return out
    V.append(task('N028V/merge_intervals','Merge overlapping or touching closed intervals [start,end]. Return intervals in start order.',
        'def solve(xs):\n    out=[]\n    for a,b in sorted(xs):\n        if out and a<=out[-1][1]: out[-1][1]=max(out[-1][1],b)\n        else: out.append([a,b])\n    return out', [[[]],[[[1,2]]],[[[1,3],[2,6],[8,9]]],[[[3,4],[1,3]]],[[[-2,5],[0,1]]]], merge, ''))
    V.append(task('N028V/decode_runs','Given pairs [text,count] with nonnegative counts, concatenate each text repeated count times.',
        'def solve(pairs):\n    return "".join(text*count for text,count in pairs)', [[[]],[[['a',3]]],[[['ab',2],['x',0],['!',1]]],[[['z',0]]]], lambda pairs:''.join(t for t,n in pairs for _ in range(n)), ''))
    def zero_sum(xs):
        return max([j-i for i in range(len(xs)) for j in range(i+1,len(xs)+1) if sum(xs[i:j])==0]+[0])
    V.append(task('N028V/zero_sum','Return the maximum length of a contiguous subarray whose sum is zero, or 0 if none.',
        'def solve(xs):\n    first={0:-1}\n    total=best=0\n    for i,x in enumerate(xs):\n        total+=x\n        if total in first: best=max(best,i-first[total])\n        else: first[total]=i\n    return best', [[[]],[[0]],[[1,-1]],[[2,-2,3,0,-3]],[[1,2,3]],[[0,0,0]]], zero_sum, ''))
    F=[]
    F.append(task('N028F/lower_bound','Given sorted list xs and value target, return the leftmost insertion index preserving sorted order.',
        'def solve(xs,target):\n    lo,hi=0,len(xs)\n    while lo<hi:\n        mid=(lo+hi)//2\n        if xs[mid]<target: lo=mid+1\n        else: hi=mid\n    return lo', [[[],3],[[1,2,2,5],2],[[1,3],0],[[1,3],8],[[2,2],2]], lambda xs,t:len([x for x in xs if x<t]), ''))
    def reachable(g,start,end):
        seen=set();todo=[start]
        while todo:
            n=todo.pop()
            if n==end:return True
            if n in seen:continue
            seen.add(n);todo.extend(g.get(n,[]))
        return False
    F.append(task('N028F/reachable','Given adjacency dictionary g and nodes start,end, return whether a directed path exists; zero edges is allowed.',
        'def solve(g,start,end):\n    seen=set()\n    todo=[start]\n    while todo:\n        n=todo.pop()\n        if n==end: return True\n        if n in seen: continue\n        seen.add(n)\n        todo.extend(g.get(n,[]))\n    return False', [[{},'a','a'],[{},'a','b'],[{'a':['b'],'b':['c']},'a','c'],[{'a':['b'],'b':['a']},'a','z']], reachable, ''))
    def brackets(s):
        stack=[];pairs={')':'(',']':'[','}':'{'}
        for c in s:
            if c in '([{':stack.append(c)
            elif c in pairs:
                if not stack or stack.pop()!=pairs[c]:return False
        return not stack
    F.append(task('N028F/brackets','Return whether brackets (),[],{} in s are balanced and properly nested. Ignore other characters.',
        'def solve(s):\n    stack=[]\n    pairs={")":"(","]":"[","}":"{"}\n    for c in s:\n        if c in "([{": stack.append(c)\n        elif c in pairs:\n            if not stack or stack.pop()!=pairs[c]: return False\n    return not stack', [[''],['a(b[c])'],['([)]'],['}'],['((a)']], brackets, ''))
    def prefix(xs):
        if not xs:return ''
        a,b=min(xs),max(xs);i=0
        while i<min(len(a),len(b)) and a[i]==b[i]:i+=1
        return a[:i]
    F.append(task('N028F/common_prefix','Return the longest common prefix of strings xs, or empty string for an empty list.',
        'def solve(xs):\n    if not xs: return ""\n    p=xs[0]\n    for s in xs[1:]:\n        while not s.startswith(p): p=p[:-1]\n    return p', [[[]],[['solo']],[['flower','flow','flight']],[['a','b']],[['','abc']]], prefix, ''))
    def grows(prefix, items):
        return [{'id':f'{prefix}/{i}','prompt':q,'answers':a if isinstance(a,list) else [a]} for i,(q,a) in enumerate(items)]
    VG=grows('N028VG', [('Responda somente com o número: 17 vezes 12.','204'),('Reply only with the integer remainder: 47 divided by 6.','5'),('Lia came before Rui. Rui came before Teo. Who came first? Reply with the name only.','Lia'),('Dê somente o plural de cão.','cães'),('Traduza blue para português. Responda uma palavra.','azul'),('What is the capital of Peru? Reply only with the city.','Lima'),('Todo peixe é um animal. Um salmão é um peixe. Um salmão é um animal? Responda apenas sim ou não.','sim'),('Qual é imutável em Python: lista ou tupla? Responda uma palavra.',['tupla','tuple'])])
    FG=grows('N028FG',[('Reply only with a number: 7 times 19.','133'),('Qual é a capital da Noruega? Apenas a cidade.','Oslo'),('Traduza thank you para português. Apenas a tradução.',['obrigado','obrigada']),('Eva está antes de Nuno, e Nuno antes de Olga. Quem é a última pessoa? Apenas o nome.','Olga')])
    probes=[{'id':'N028UT/0','prompt':'Use run_python to compute 53 times 27. Then reply only with the result.','expected':'1431'}, {'id':'N028UT/1','prompt':'Use run_python to compute the average of [5,7,9]. Fix the previous failed call and reply only with the result.','expected':'7','prior_failed_call':'print((5+7)/0)'}]
    save('train_code.json',T);save('train_general.json',G);save('train_tools.json',U);save('anchors.json',A);save('validation_code.json',V);save('validation_general.json',VG);save('final_code.json',F);save('final_general.json',FG);save('tool_probes.json',probes);save('schemas.json',schemas);save('tool_observations.json',{'sum_cubes':obs,'failed':bad,'repair':fixed})
    assert len(T)+len(G)+len(U)==48
    train_text={r['prompt'] for r in T+G}|{m['content'] for r in U for m in r['messages'] if m['role']=='user'}
    assert not train_text & {r['prompt'] for r in V+F+VG+FG+probes}
    assert not {r['family'] for r in T} & {r['family'] for r in V+F}
    save('construction_audit.json',{'train_code':len(T),'train_general':len(G),'train_tools':len(U),'paired_views':96,'anchors':len(A),'validation_code':len(V),'validation_cases':sum(len(r['cases']) for r in V),'sealed_final_code':len(F),'sealed_final_cases':sum(len(r['cases']) for r in F),'references_all_passed':True,'None_mutants_rejected':True,'tool_observations_real_restricted_execution':True,'exact_prompt_overlap':False,'algorithm_label_overlap_train_to_validation_final':False,'pretraining_or_ordinary_skill_overlap_not_ruled_out':True,'no_model_outputs_used_to_author_or_select_tests':True})
    print('DATA028_COMPLETE',len(T),len(G),len(U),flush=True)


if __name__=='__main__': main()
