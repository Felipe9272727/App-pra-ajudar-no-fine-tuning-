"""Fresh executable tasks. Reference functions build test oracles, never prompts."""
import collections
import hashlib
import json
import math
from pathlib import Path
import random
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'code_rsi'
rng=random.Random(2026110408)
rows=[]
def add(key,sig,description,fn,args):
    cases=[]
    for a in args:
        expected=fn(*a)
        cases.append({'args':a,'expected':expected})
    rows.append({'id':key,'signature':sig,'prompt':f'Write Python 3 function {sig}. {description} Return only the complete function, without explanations, examples or tests. Do not print. Do not use imports.','cases':cases})
# Adaptation: test rewards and model-produced activations only.
add('sum_abs','solve(xs)','Return the sum of absolute values in the integer list xs; empty gives 0.',lambda x:sum(abs(v) for v in x),[[[]],[[1,-2,3]],[[-8,-8]],[[0]],[[4,-4,5,-9]]])
add('clamp','solve(x, lo, hi)','Return x restricted to the inclusive range lo through hi, where lo <= hi.',lambda x,l,h:max(l,min(h,x)),[[2,0,5],[-4,0,5],[9,0,5],[3,3,3],[-9,-6,-2]])
add('count_even','solve(xs)','Return how many integers in xs are even, including zero.',lambda x:sum(v%2==0 for v in x),[[[]],[[0,1,2,3]],[[-2,-3,8]],[[1,3,5]],[[4,4]]])
add('palindrome','solve(s)','Return whether string s reads the same forwards and backwards, case sensitive.',lambda s:s==s[::-1],[[''],['aba'],['ab'],['Aba'],['12321'],['aa']])
add('prefix_sums','solve(xs)','Return a list containing the running sums of xs. Empty gives an empty list.',lambda x:[sum(x[:i+1]) for i in range(len(x))],[[[]],[[2,3,-1]],[[0]],[[5,-5,8]],[[1,1,1]]])
add('dedup_stable','solve(xs)','Return the elements of xs with duplicates removed, preserving first occurrence order.',lambda x:list(dict.fromkeys(x)),[[[]],[[3,1,3,2,1]],[[0,0]],[[-1,2,-1]],[[4,3,2,1]]])
add('overlap_count','solve(s, sub)','Return the number of overlapping occurrences of the nonempty substring sub in s.',lambda s,t:sum(s[i:i+len(t)]==t for i in range(len(s)-len(t)+1)),[['aaaa','aa'],['banana','ana'],['abc','x'],['','a'],['ababa','aba']])
add('run_lengths','solve(s)','Return a list of run lengths of consecutive identical characters in s. Empty gives an empty list.',lambda s:[len(list(g)) for _,g in __import__('itertools').groupby(s)],[[''],['aaabbc'],['abcd'],['zzzz'],['aabba']])
# Development: task specifications differ from adaptation.
add('sum_positive','solve(xs)','Return the sum of strictly positive numbers in xs.',lambda x:sum(v for v in x if v>0),[[[]],[[-3,4,0,2]],[[1,2,3]],[[-1,-2]],[[7,-7,8]]])
add('rotate_right','solve(xs, k)','Return a new list rotating xs right by nonnegative k places; handle empty xs.',lambda x,k:x[-(k%len(x)):]+x[:-(k%len(x))] if x and k%len(x) else x,[[[],4],[[1,2,3],1],[[1,2,3],3],[[5],8],[[1,2,3,4],6]])
add('first_unique','solve(s)','Return the first character appearing exactly once in s, or the empty string if none exists.',lambda s:next((c for c in s if s.count(c)==1),''),[[''],['swiss'],['aabb'],['level'],['abc']])
add('pair_count','solve(xs, target)','Count index pairs i < j for which xs[i] + xs[j] equals target.',lambda x,t:sum(x[i]+x[j]==t for i in range(len(x)) for j in range(i+1,len(x))),[[[],2],[[1,1,2,3],4],[[2,2,2],4],[[-1,0,1],0],[[4],8]])
add('char_counts','solve(s)','Return a dictionary mapping each character in s to its frequency.',lambda s:dict(collections.Counter(s)),[[''],['banana'],['a a'],['ABC'],['xxxy']])
add('longest_run','solve(xs)','Return the maximum length of a run of equal consecutive elements in xs, or 0 if empty.',lambda x:max([len(list(g)) for _,g in __import__('itertools').groupby(x)] or [0]),[[[]],[[1,1,2,2,2,1]],[[3]],[[1,2,3]],[[0,0,0,0]]])
add('binary_search','solve(xs, target)','Given sorted distinct integers xs, return the index of target or -1 if absent.',lambda x,t:x.index(t) if t in x else -1,[[[],2],[[1,3,5],3],[[1,3,5],4],[[-3,0,7],-3],[[4],4]])
add('flatten_once','solve(xss)','Flatten a list of lists by one level, returning one list.',lambda xx:[v for x in xx for v in x],[[[]],[[[1,2],[],[3]]],[[[],[]]],[[['a'],['b','c']]],[[[0]]]])
# Validation, separate tasks, never used to fit neuron scores.
add('divisible_sum','solve(xs, k)','Return the sum of elements of xs divisible by positive k.',lambda x,k:sum(v for v in x if v%k==0),[[[],3],[[1,3,6,8],3],[[-4,0,2,5],2],[[7,14],7],[[1,2,3],9]])
add('reverse_words','solve(s)','Return the whitespace-separated words of s in reverse order, joined by single spaces.',lambda s:' '.join(s.split()[::-1]),[[''],['a b c'],['  hello   world '],['one'],['x\ty\nz']])
add('gcd','solve(a, b)','Return the nonnegative greatest common divisor of integers a and b.',math.gcd,[[0,0],[12,18],[-8,12],[17,13],[0,-9]])
def balanced(s):
    stack=[];pairs={')':'(',']':'[','}':'{'}
    for c in s:
        if c in '([{':stack.append(c)
        elif not stack or stack.pop()!=pairs[c]:return False
    return not stack
add('balanced','solve(s)','Return whether a string containing only ()[]{} brackets is correctly balanced and nested.',balanced,[[''],['([]){}'],['([)]'],['(('],['}{'],['()']])
add('transpose','solve(matrix)','Transpose a nonempty rectangular matrix, returning a list of lists.',lambda m:[list(x) for x in zip(*m)],[[[[1,2],[3,4]]],[[[1,2,3]]],[[[1],[2],[3]]],[[[0]]]])
add('intersection','solve(a, b)','Return a sorted list of distinct values appearing in both integer lists a and b.',lambda a,b:sorted(set(a)&set(b)),[[[],[]],[[3,1,1,2],[2,3,3]],[[-1,2],[-1]],[[1],[2]],[[5,5],[5]]])
add('second_largest','solve(xs)','Return the second largest distinct integer in xs, or None if fewer than two distinct integers exist.',lambda x:sorted(set(x))[-2] if len(set(x))>=2 else None,[[[]],[[4,4]],[[1,5,3,5]],[[-5,-1,-3]],[[0,1]]])
add('merge_sorted','solve(a, b)','Merge two sorted integer lists into one sorted list, keeping duplicates.',lambda a,b:sorted(a+b),[[[],[]],[[1,3],[2,4]],[[1,1],[1]],[[5],[]],[[-3,0],[-2,7]]])
# Final test: distinct tasks, fixed before any outputs.
add('even_squares','solve(xs)','Return squares of even integers in xs, preserving their order.',lambda x:[v*v for v in x if v%2==0],[[[]],[[1,2,-4,3,0]],[[3,5]],[[8]],[[2,2]]])
add('median','solve(xs)','Return the median of a nonempty integer list, averaging the middle pair for even length.',lambda x:__import__('statistics').median(x),[[[1]],[[3,1,2]],[[1,4,2,3]],[[-8,-2]],[[0,0,1]]])
add('digit_sum','solve(n)','Return the sum of decimal digits in integer n, ignoring its sign.',lambda n:sum(map(int,str(abs(n)))),[[0],[123],[-901],[7777],[10020]])
add('factorial','solve(n)','Return n factorial for a nonnegative integer n, with 0 factorial equal to 1.',math.factorial,[[0],[1],[5],[7],[3]])
add('is_prime','solve(n)','Return whether integer n is prime.',lambda n:n>=2 and all(n%d for d in range(2,math.isqrt(n)+1)),[[-3],[0],[2],[17],[49],[91]])
add('fibonacci','solve(n)','Return Fibonacci number F(n), where F(0)=0 and F(1)=1, for nonnegative n.',lambda n:round(((1+5**.5)/2)**n/5**.5),[[0],[1],[2],[7],[15]])
add('word_lengths','solve(s)','Return the lengths of whitespace-separated words in s as a list.',lambda s:[len(w) for w in s.split()],[[''],['ab c def'],['  one   two '],['x'],['a\nbb']])
add('nonzero','solve(xs)','Return a list containing only the nonzero elements of xs, preserving order.',lambda x:[v for v in x if v!=0],[[[]],[[0,1,0,-2]],[[0,0]],[[3]],[[False,2]]])
add('argmax','solve(xs)','Return the index of the first maximum value in nonempty xs.',lambda x:x.index(max(x)),[[[3]],[[1,5,5,2]],[[-3,-1,-4]],[[0,0]],[[9,2,1]]])
add('cumulative_product','solve(xs)','Return the running products of xs as a list; empty gives an empty list.',lambda x:[math.prod(x[:i+1]) for i in range(len(x))],[[[]],[[2,3,4]],[[0,2]],[[3,-2,1]],[[1]]])
add('anagram','solve(a, b)','Return whether strings a and b are anagrams, case sensitive and counting spaces.',lambda a,b:sorted(a)==sorted(b),[['',''],['listen','silent'],['aab','abb'],['A','a'],['ab ',' ba']])
add('max_subarray','solve(xs)','Return the maximum sum of a nonempty contiguous subarray of nonempty xs.',lambda x:max(sum(x[i:j]) for i in range(len(x)) for j in range(i+1,len(x)+1)),[[[1,-2,3,4,-1]],[[-5,-2,-9]],[[3]],[[0,0]],[[-1,2,-1,2]]])
add('chunk','solve(xs, k)','Split xs into consecutive chunks of positive size k; the last may be shorter.',lambda x,k:[x[i:i+k] for i in range(0,len(x),k)],[[[],3],[[1,2,3,4,5],2],[[1,2],9],[[0,1],1],[[4,4,4],2]])
add('strip_vowels','solve(s)','Remove all ASCII vowels aeiouAEIOU from s, preserving other characters.',lambda s:''.join(c for c in s if c not in 'aeiouAEIOU'),[[''],['Hello WORLD'],['AEiou'],['xyz'],['a1e!']])
add('hamming','solve(a, b)','Return the number of differing positions in equal-length strings a and b.',lambda a,b:sum(x!=y for x,y in zip(a,b)),[['',''],['abc','adc'],['000','111'],['same','same'],['Ab','ab']])
add('missing_number','solve(xs, n)','xs contains distinct integers from 0 through n with exactly one missing. Return it.',lambda x,n:n*(n+1)//2-sum(x),[[[],0],[[0,1,3],3],[[1,2],2],[[0,1],2],[[0,2,3,4],4]])
add('rle_text','solve(s)','Run-length encode s by writing each character followed by its run length. Empty gives an empty string.',lambda s:''.join(c+str(len(list(g))) for c,g in __import__('itertools').groupby(s)),[[''],['aaabb'],['abc'],['zzzz'],['aabbaa']])
add('is_sorted','solve(xs)','Return whether xs is nondecreasing.',lambda x:all(x[i]<=x[i+1] for i in range(len(x)-1)),[[[]],[[1]],[[1,1,2]],[[2,1]],[[0,-1,2]]])
add('partition','solve(xs, pivot)','Return two lists: values below pivot, then values at least pivot. Preserve order within each list.',lambda x,p:[[v for v in x if v<p],[v for v in x if v>=p]],[[[],2],[[3,1,2,0],2],[[1,1],1],[[-2,0],-1],[[8],9]])
add('find_all','solve(xs, target)','Return all indices at which target appears in xs.',lambda x,t:[i for i,v in enumerate(x) if v==t],[[[],1],[[1,2,1],1],[[0,0],0],[[3],4],[[4,3,4,4],4]])
add('remove_adjacent_duplicates','solve(s)','Collapse each run of repeated consecutive characters in s into one character.',lambda s:''.join(c for c,_ in __import__('itertools').groupby(s)),[[''],['aaabbca'],['abba'],['xy'],['zzzz']])
add('to_base_two','solve(n)','Return the base-two representation of nonnegative integer n as a string, without a prefix.',lambda n:bin(n)[2:],[[0],[1],[2],[13],[32]])
add('caesar','solve(s, k)','Shift lowercase ASCII letters forward by k modulo 26, preserving all other characters.',lambda s,k:''.join(chr((ord(c)-97+k)%26+97) if 'a'<=c<='z' else c for c in s),[['',3],['xyz',2],['abc',26],['a Z!',-1],['hello',13]])
add('unique_words','solve(s)','Return a sorted list of distinct whitespace-separated words in s, case sensitive.',lambda s:sorted(set(s.split())),[[''],['b a b c'],['A a A'],[' x  x '],['one']])
assert len(rows)==48
controls=[('dev','What is the chemical symbol for antimony? Reply only with the symbol.','Sb'),('dev','What is the plural of child? Reply with one word.','children'),('dev','What is the capital of Chile? Reply only with the city.','Santiago'),('dev','What organ pumps blood? Reply with one word.','heart'),('val','What is the chemical symbol for copper? Reply only with the symbol.','Cu'),('val','What is the plural of mouse? Reply with one word.','mice'),('val','What is the capital of Estonia? Reply only with the city.','Tallinn'),('val','How many sides does a triangle have? Reply with an integer.','3'),('test','What is the chemical symbol for helium? Reply only with the symbol.','He'),('test','What is the plural of foot? Reply with one word.','feet'),('test','What is the capital of Kenya? Reply only with the city.','Nairobi'),('test','Give the opposite of fragile. Reply with one word.','robust'),('test','What is the past tense of teach? Reply with one word.','taught'),('test','Which gas do plants absorb for photosynthesis? Reply only with its chemical formula.','CO2'),('test','What is the chemical symbol for lead? Reply only with the symbol.','Pb'),('test','What is the capital of Argentina? Reply only with the city.','Buenos Aires')]
data={'version':'code-outcome-only-v1','seed':2026110408,'train':rows[:8],'development':rows[8:16],'validation':rows[16:24],'heldout':rows[24:],'controls':{s:[{'id':s+'_'+str(i),'question':q,'answer':a,'aliases':['sturdy','strong','durable'] if a=='robust' else [],'numeric':a.isdigit()} for i,(split,q,a) in enumerate(controls) if split==s] for s in ['dev','val','test']},'anchors':json.loads((ROOT/'history/pilot1_data.json').read_text())['anchors'],'protocol':{'feedback':'execution status and fraction passed, no expected output, no reference solution or target-token supervision','max_new_tokens':160,'thinking_probe_tokens':160,'repair_budget':2,'loop_counts':[2,3,4],'late_visit_total_gain':0.05,'channel_edit_fraction':0.03,'max_parallel_jobs':4,'anchor_nll_ratio_cap':1.02,'promotion':'strict increase in tasks passing all tests; no loss in general controls; anchors <= 102% baseline; validation confirms before final test','benchmark':'custom 48-task Python pilot, not evidence of best small coding model','test_answer_in_prompt':False}}
(HERE/'data.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
(HERE/'SHA256SUMS').write_text(''.join(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()+'  '+p+'\n' for p in ['checkpoints/liquid_patch.pt','code_rsi/data.json']))
if __name__=='__main__':print({k:len(data[k]) for k in ['train','development','validation','heldout']})
