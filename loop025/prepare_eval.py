"""Freeze new custom validation/final suites; references stay outside inference."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from local_cpu.sandbox import evaluate
H=ROOT/'loop025'
def row(id,family,prompt,solution,inputs,oracle):
 r={'id':id,'family':family,'prompt':prompt+' Return only the function, without imports or explanation.','solution':solution,'cases':[{'args':[x],'expected':oracle(x)} for x in inputs],'provenance':'new researcher-authored025custom task; not a published benchmark; no model outputs used in construction'}
 a=evaluate(solution,r);assert a['all_passed'],(id,a)
 b=evaluate('def solve(x):\n    return None\n',r);assert not b['all_passed'];return r
val=[]
val.append(row('L025V/rotate','rotation','Write Python function solve(xs). Rotate list xs left by exactly three positions with wraparound. Return [] for an empty list.','def solve(xs):\n    if not xs: return []\n    k = 3 % len(xs)\n    return xs[k:] + xs[:k]\n',[[],[1],[2,3],[0,1,2],[0,1,2,3],[1,2,3,4,5,6],[-3,-2,-1,0,1],['a','b'],[1,1,2,2]],lambda x:x[3%len(x):]+x[:3%len(x)] if x else []))
def bracket(s):
 st=[];pairs={')':'(',']':'[','}':'{'}
 for c in s:
  if c in '([{':st.append(c)
  elif c in pairs:
   if not st or st.pop()!=pairs[c]:return False
 return not st
val.append(row('L025V/brackets','stack_validation','Write Python function solve(s). Return whether (), [] and {} brackets are properly nested and matched. Ignore other characters. Empty input is valid.','def solve(s):\n    stack=[]\n    pairs={")":"(", "]":"[", "}":"{"}\n    for c in s:\n        if c in "([{": stack.append(c)\n        elif c in pairs:\n            if not stack or stack.pop()!=pairs[c]: return False\n    return not stack\n',['','abc','()','([{}])','([)]',')(','{a[b(c)d]e}','(((',']','{}[]()'],bracket))
val.append(row('L025V/compact','adjacent_compaction','Write Python function solve(xs). Collapse each maximal run of equal adjacent elements to one element, preserving order. Do not remove equal elements separated by other values.','def solve(xs):\n    out=[]\n    for x in xs:\n        if not out or out[-1]!=x: out.append(x)\n    return out\n',[[],[1],[1,1,1],[1,2,1],[1,1,2,2,1,1],[0,0,-1,-1,0],['a','a','b','a'],[False,False,True]],lambda x:[v for i,v in enumerate(x) if i==0 or v!=x[i-1]]))
def subarray(x):return max([0]+[sum(x[a:b]) for a in range(len(x)) for b in range(a+1,len(x)+1)])
val.append(row('L025V/subarray','kadane','Write Python function solve(xs). Return the maximum sum of any contiguous subarray of integer list xs. The empty subarray is allowed with sum 0.','def solve(xs):\n    best=cur=0\n    for x in xs:\n        cur=max(0,cur+x)\n        best=max(best,cur)\n    return best\n',[[],[-5],[3],[-2,-1,-3],[1,-2,3,4,-1],[-3,5,-2,6,-9],[0,0],[4,-10,5,6],[2,-1,2,-1,2]],subarray))
final=[]
def zeros(n):
 p=1
 for x in range(1,n+1):p*=x
 s=str(p);return len(s)-len(s.rstrip('0'))
final.append(row('L025T/zeros','factorial_divisibility','Write Python function solve(n). For a nonnegative integer n, return the number of trailing decimal zero digits of n!. Handle n=0.','def solve(n):\n    total=0\n    while n:\n        n//=5\n        total+=n\n    return total\n',[0,1,4,5,9,10,24,25,30,50,125],zeros))
final.append(row('L025T/transpose','matrix_transpose','Write Python function solve(rows). Transpose a rectangular list of lists, returning lists rather than tuples. Return [] if there are no rows or zero columns.','def solve(rows):\n    if not rows or not rows[0]: return []\n    return [[row[i] for row in rows] for i in range(len(rows[0]))]\n',[[],[[]],[[],[]],[[1]],[[1,2,3]],[[1],[2],[3]],[[1,2],[3,4]],[[0,-1,2],[3,4,5]]],lambda x:[list(y) for y in zip(*x)] if x else []))
final.append(row('L025T/unique','stable_distinct','Write Python function solve(xs). Remove duplicate integer values globally, retaining only their first occurrence in the original order.','def solve(xs):\n    out=[]\n    seen=set()\n    for x in xs:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n',[[],[1],[1,1],[1,2,1],[3,1,3,2,1],[-1,0,-1,2,0],[0]*8],lambda x:list(dict.fromkeys(x))))
def merged(xs):
 out=[]
 for a,b in sorted(xs):
  if out and a<=out[-1][1]:out[-1][1]=max(out[-1][1],b)
  else:out.append([a,b])
 return out
final.append(row('L025T/intervals','interval_union','Write Python function solve(intervals). Each input interval [start,end] has start<=end. Merge overlapping or endpoint-touching closed intervals, returning sorted [start,end] lists. Do not mutate the input.','def solve(intervals):\n    out=[]\n    for a,b in sorted(intervals):\n        if out and a<=out[-1][1]: out[-1][1]=max(out[-1][1],b)\n        else: out.append([a,b])\n    return out\n',[[],[[1,2]],[[3,5],[1,3]],[[1,10],[2,3]],[[1,2],[4,5]],[[0,0],[0,1],[2,2]],[[5,8],[-2,3],[2,6]]],merged))
new_general=[{'id':'L025G/00','question':'Reply with one word: what is the plural of goose?','answer':'geese','aliases':[],'numeric':False},{'id':'L025G/01','question':'Responda somente com o número: 13 vezes 6.','answer':'78','aliases':[],'numeric':True},{'id':'L025G/02','question':'Reply only with the symbol: chemical symbol for potassium.','answer':'K','aliases':[],'numeric':False},{'id':'L025G/03','question':'Nina veio antes de Otto. Otto veio antes de Paula. Quem veio primeiro? Responda apenas o nome.','answer':'Nina','aliases':[],'numeric':False}]
for name,rows in [('validation',val),('final',final),('final_general',new_general)]:
 p=H/(name+'.json');assert not p.exists();p.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
a={'custom_validation_tasks':len(val),'custom_final_tasks':len(final),'reference_cases':sum(len(r['cases']) for r in val+final),'all_reference_solutions_passed':True,'all_None_mutants_rejected':True,'no_model_outputs_observed':True,'families_disjoint_between_train_validation_final':True,'ordinary_skill_overlap_possible':True};(H/'reference_audit.json').write_text(json.dumps(a,indent=2)+'\n');print(a)
