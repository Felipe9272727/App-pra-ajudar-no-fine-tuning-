"""Observed tasks are search curriculum; new tasks gate transfer and final report."""
import collections,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'rsi100'
prior=json.loads((ROOT/'code_rsi/data.json').read_text());rows=[]
def add(key,sig,text,fn,args):
 rows.append({'id':'r100_'+key,'signature':sig,'prompt':f'Write Python 3 function {sig}. {text} Return only the complete function, without explanations, examples or tests. Do not print. Do not use imports.','cases':[{'args':a,'expected':fn(*a)} for a in args]})
# Eight new tasks: one final promotion gate, not the 100-round reward.
add('sum_cubes','solve(xs)','Return the sum of the cubes of the integers in xs.',lambda x:sum(v**3 for v in x),[[[]],[[1,2]],[[-2,3]],[[0]],[[4,-4]]])
add('count_negative','solve(xs)','Count how many integers in xs are strictly negative.',lambda x:sum(v<0 for v in x),[[[]],[[-1,0,2,-3]],[[1,2]],[[-8,-8]],[[0]]])
add('word_prefix','solve(s, prefix)','Return the whitespace-separated words of s starting with prefix, as a list in original order.',lambda s,p:[w for w in s.split() if w.startswith(p)],[['','a'],['apple ape bat','ap'],[' a ab b ','a'],['cat','x'],['one two','']])
add('adjacent_changes','solve(xs)','Return how many adjacent pairs in xs have different values.',lambda x:sum(a!=b for a,b in zip(x,x[1:])),[[[]],[[1]],[[1,1,2,2,3]],[[1,2,1]],[[0,0]]])
add('absolute_differences','solve(xs)','Return absolute differences between consecutive elements of xs as a list.',lambda x:[abs(a-b) for a,b in zip(x,x[1:])],[[[]],[[1]],[[4,1,5]],[[-3,2,0]],[[8,8]]])
add('repeat_words','solve(words, n)','Return a list repeating each string in words n consecutive times, with n nonnegative.',lambda x,n:[w for w in x for _ in range(n)],[[[],3],[['a','b'],2],[['x'],0],[['a','a'],1],[['hi'],3]])
add('closed_range_filter','solve(xs, lo, hi)','Return values in xs between lo and hi inclusive, preserving order.',lambda x,l,h:[v for v in x if l<=v<=h],[[[],0,3],[[-1,0,2,4],0,2],[[3,3],3,3],[[1,2],4,8],[[-2,-1],-3,0]])
add('reverse_each_word','solve(s)','Reverse the characters of every whitespace-separated word, joining them with single spaces.',lambda s:' '.join(w[::-1] for w in s.split()),[[''],['ab cd'],['  hello world '],['x'],['one\ntwo']])
# Sixteen final tasks, all distinct from the preceding 48-task pilot.
add('symmetric_difference','solve(a, b)','Return a sorted list of values occurring in exactly one of integer lists a and b.',lambda a,b:sorted(set(a)^set(b)),[[[],[]],[[1,2],[2,3]],[[1,1],[]],[[-1,0],[0,2]],[[3],[3]]])
add('dot_product','solve(a, b)','Return the dot product of equal-length lists a and b; empty gives 0.',lambda a,b:sum(x*y for x,y in zip(a,b)),[[[],[]],[[1,2],[3,4]],[[-2,0],[5,9]],[[3],[2]],[[0,0],[1,2]]])
add('lcm','solve(a, b)','Return the nonnegative least common multiple of integers a and b, or 0 if either is zero.',math.lcm,[[0,2],[4,6],[-3,5],[7,7],[0,0]])
add('largest_sorted_gap','solve(xs)','Return the largest difference between consecutive values after sorting xs; return 0 for fewer than two values.',lambda x:max([b-a for a,b in zip(sorted(x),sorted(x)[1:])] or [0]),[[[]],[[8]],[[5,1,9]],[[-3,-1,6]],[[2,2,2]]])
add('count_digits','solve(s)','Count ASCII decimal digits 0 through 9 in s.',lambda s:sum('0'<=c<='9' for c in s),[[''],['a1b23'],['abc'],['0-9'],['１２3']])
add('string_chunks','solve(s, k)','Split string s into consecutive substrings of positive size k, returning a list.',lambda s,k:[s[i:i+k] for i in range(0,len(s),k)],[['',2],['abcde',2],['ab',8],['abc',1],['aaaa',3]])
add('argmin','solve(xs)','Return the index of the first minimum value in nonempty xs.',lambda x:x.index(min(x)),[[[1]],[[3,1,1,2]],[[-3,0,-2]],[[0,0]],[[9,3,5]]])
add('unique_count','solve(xs)','Return the number of distinct values in xs.',lambda x:len(set(x)),[[[]],[[1,1,2]],[[0,0]],[[-1,0,1]],[[3]]])
add('first_multiples','solve(k, n)','Return the first n positive-index multiples of k: k, 2*k, and so on, with n nonnegative.',lambda k,n:[k*i for i in range(1,n+1)],[[3,0],[2,4],[-3,3],[0,3],[7,1]])
def common_prefix(a,b):
 i=0
 while i<min(len(a),len(b)) and a[i]==b[i]:i+=1
 return a[:i]
add('common_prefix','solve(a, b)','Return the longest common prefix of strings a and b.',common_prefix,[['','abc'],['flower','flow'],['abc','xyz'],['same','same'],['a','ab']])
add('pairwise_products','solve(xs)','Return products of each adjacent pair in xs as a list.',lambda x:[a*b for a,b in zip(x,x[1:])],[[[]],[[2]],[[2,3,4]],[[-2,0,5]],[[1,1,1]]])
add('rectangle_perimeter','solve(width, height)','Return the perimeter of a rectangle with nonnegative width and height.',lambda w,h:2*(w+h),[[0,0],[3,4],[0,5],[2,2],[1.5,2.5]])
add('triangular','solve(n)','Return the sum of integers from 1 through nonnegative n, with 0 giving 0.',lambda n:n*(n+1)//2,[[0],[1],[5],[10],[100]])
add('word_count_map','solve(s)','Return a dictionary of frequencies of whitespace-separated words in s, case sensitive.',lambda s:dict(collections.Counter(s.split())),[[''],['a b a'],[' A a A '],['one'],['x\nx']])
add('wrap_index','solve(xs, i)','Return xs[i modulo len(xs)] for a nonempty list xs and any integer i.',lambda x,i:x[i%len(x)],[[[1,2,3],4],[[8],-9],[[1,2,3],-1],[[4,5],0],[[2,3],10]])
add('keep_every_nth','solve(xs, n)','Return every nth element of xs starting with index zero, with n positive.',lambda x,n:x[::n],[[[],2],[[0,1,2,3,4],2],[[1,2],1],[[3,4],8],[[1,2,3,4,5,6],3]])
assert len(rows)==24
controls=[{'id':'search_ctl_'+str(i),**r} for i,r in enumerate(prior['controls']['dev'])]
newcontrols=[('val','What is the chemical symbol for neon? Reply only with the symbol.','Ne'),('val','What is the plural of wolf? Reply with one word.','wolves'),('val','What is the capital of Sweden? Reply only with the city.','Stockholm'),('val','Give the opposite of temporary. Reply with one word.','permanent'),('test','What is the chemical symbol for zinc? Reply only with the symbol.','Zn'),('test','What is the plural of person? Reply with one word.','people'),('test','What is the capital of Poland? Reply only with the city.','Warsaw'),('test','What is the past tense of write? Reply with one word.','wrote'),('test','What is the chemical symbol for magnesium? Reply only with the symbol.','Mg'),('test','What is the capital of Finland? Reply only with the city.','Helsinki'),('test','Give the opposite of optional. Reply with one word.','mandatory'),('test','What is the past tense of drive? Reply with one word.','drove')]
data={'seed':20261104100,'search':prior['train'],'guard':prior['development'],'validation':rows[:8],'heldout':rows[8:],'search_controls':controls,'controls':{s:[{'id':'r100_'+s+'_'+str(i),'question':q,'answer':a,'numeric':False} for i,(sp,q,a) in enumerate(newcontrols) if sp==s] for s in ['val','test']},'anchors':prior['anchors'],'protocol':{'rounds':100,'chunk_size':10,'internal_pass_counts':[2,3,4],'max_new_tokens':160,'feedback':'execution outcomes only; no reference solutions or target token loss','accept':'no previously correct search/guard test lost, at least one new test passed, no control answer lost and no increase in anchor NLL','rejected_weights':'restore incumbent and remove uncommitted candidate; keep audit metrics and mutation seed','search_overfit':'100 decisions reuse explicitly observed search/guard curriculum; these are not heldout scores','final_test_for_selection':False}}
(HERE/'data.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
(HERE/'SHA256SUMS').write_text(''.join(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()+'  '+p+'\n' for p in ['checkpoints/liquid_patch.pt','code_rsi/checkpoints/activation_summary.pt','rsi100/data.json']))
print({k:len(data[k]) for k in ['search','guard','validation','heldout']})
