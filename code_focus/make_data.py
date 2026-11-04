"""Reference functions build tests only; no solutions in the model prompts."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'code_focus';old=json.loads((ROOT/'code_rsi/data.json').read_text());rows=[]
def add(name,sig,text,fn,args):
 rows.append({'id':'focus_'+name,'signature':sig,'prompt':f'Write Python 3 function {sig}. {text} Return only the complete function, without explanations, examples or tests. Do not print. Do not use imports.','cases':[{'args':a,'expected':fn(*a)} for a in args]})
add('suffix_sums','solve(xs)','Return a list whose element i is the sum of xs from index i to the end.',lambda x:[sum(x[i:]) for i in range(len(x))],[[[]],[[1,2,3]],[[-2,4,-1]],[[0]],[[5,-5]]])
add('overlap_positions','solve(s, sub)','Return all starting indices of occurrences of nonempty sub in s, including overlapping occurrences.',lambda s,t:[i for i in range(len(s)-len(t)+1) if s[i:i+len(t)]==t],[['aaaa','aa'],['banana','ana'],['','x'],['abc','d'],['ababa','aba']])
add('run_values','solve(s)','Return a list containing the character of each consecutive run of equal characters in s.',lambda s:[c for i,c in enumerate(s) if i==0 or c!=s[i-1]],[[''],['aaabbca'],['abba'],['zz'],['abc']])
add('rotate_left','solve(xs, k)','Rotate list xs left by nonnegative k places, wrapping around. Return a new list and handle empty xs.',lambda x,k:x[k%len(x):]+x[:k%len(x)] if x else [],[[[],4],[[1,2,3],1],[[1,2,3],3],[[4],9],[[1,2,3,4],6]])
def longest_increasing(x):
 best=curr=0;last=None
 for v in x:
  curr=curr+1 if last is not None and v>last else 1;best=max(best,curr);last=v
 return best
add('longest_increasing_run','solve(xs)','Return the length of the longest contiguous strictly increasing run in xs; empty gives 0.',longest_increasing,[[[]],[[1]],[[3,1,2,3]],[[1,2,1,2,3,4]],[[4,3,2]],[[1,1,2]]])
add('parenthesis_prefix_balances','solve(s)','For a string containing only parentheses, return a list of prefix balances: opening adds one and closing subtracts one.',lambda s:[sum(1 if c=='(' else -1 for c in s[:i+1]) for i in range(len(s))],[[''],['()'],['(())'],['))(('],['(((']])
add('moving_sums','solve(xs, k)','Return sums of all consecutive complete windows of positive length k in xs. If no complete window exists, return an empty list.',lambda x,k:[sum(x[i:i+k]) for i in range(len(x)-k+1)],[[[],2],[[1,2,3,4],2],[[2,-2,3],1],[[1,2],3],[[4,5],2]])
add('frequency_per_position','solve(xs)','Return a list containing, at each position, how many times that value appears anywhere in xs.',lambda x:[x.count(v) for v in x],[[[]],[[1,2,1]],[[3,3,3]],[[0,-1,0,2]],[[5]]])
add('prefix_minima','solve(xs)','Return the running minimum at every position of xs as a list. Empty gives an empty list.',lambda x:[min(x[:i+1]) for i in range(len(x))],[[[]],[[4,2,3,1]],[[-2,0,-3]],[[5]],[[1,1,2]]])
add('suffix_maxima','solve(xs)','Return the maximum from each position through the end of xs as a list.',lambda x:[max(x[i:]) for i in range(len(x))],[[[]],[[1,4,2,3]],[[-5,-2,-8]],[[0]],[[3,3]]])
def longest_run_start(x):
 if not x:return -1
 best_start=0;best_len=0;start=0
 for i in range(len(x)+1):
  if i==len(x) or x[i]!=x[start]:
   if i-start>best_len:best_start,best_len=start,i-start
   start=i
 return best_start
add('longest_run_start','solve(xs)','Return the starting index of the longest run of equal consecutive values in xs; choose the earliest on ties, or -1 if empty.',longest_run_start,[[[]],[[1]],[[1,2,2,2]],[[3,3,1,1]],[[1,2,3,3,3]]])
add('ordered_character_pairs','solve(s, a, b)','Count pairs of indices i < j where s[i] equals character a and s[j] equals character b.',lambda s,a,b:sum(s[i]==a and s[j]==b for i in range(len(s)) for j in range(i+1,len(s))),[['','a','b'],['abab','a','b'],['aaa','a','a'],['ba','a','b'],['aabb','a','b']])
add('longest_zero_run','solve(xs)','Return the length of the longest contiguous run of zeroes in integer list xs.',lambda x:max([len(g) for g in ''.join('0' if v==0 else 'x' for v in x).split('x')] or [0]),[[[]],[[0,0,1,0]],[[2,3]],[[1,0,0,0]],[[0]]])
add('rotate_text_right','solve(s, k)','Return string s rotated right by nonnegative k characters, wrapping around; handle an empty string.',lambda s,k:s[-(k%len(s)):]+s[:-(k%len(s))] if s and k%len(s) else s,[['',5],['abcd',1],['abc',3],['x',8],['abcde',7]])
add('last_unique_character','solve(s)','Return the last character of s occurring exactly once in s, or an empty string if none.',lambda s:next((c for c in reversed(s) if s.count(c)==1),''),[[''],['swiss'],['aabb'],['abca'],['xyz']])
add('gap_indices','solve(xs)','Return indices i greater than zero where xs[i] minus xs[i-1] is greater than one.',lambda x:[i for i in range(1,len(x)) if x[i]-x[i-1]>1],[[[]],[[1]],[[1,2,5,3,8]],[[0,0,1]],[[-4,-1,2]]])
prose=['Describe a quiet library in three short sentences.','Explain why people keep calendars in three short sentences.','Describe a rainy afternoon in three short sentences.','Explain how a bicycle is useful in three short sentences.','Describe a friendly neighborhood in three short sentences.','Explain why plants need water in three short sentences.','Describe a mountain path in three short sentences.','Explain how a shared meal can bring people together in three short sentences.']
ctl=[('val','What is the capital of Lithuania? Reply only with the city.','Vilnius'),('val','What is the chemical symbol for xenon? Reply only with the symbol.','Xe'),('val','What is the plural of analysis? Reply with one word.','analyses'),('val','Give the opposite of opaque. Reply with one word.','transparent'),('test','What is the capital of Latvia? Reply only with the city.','Riga'),('test','What is the chemical symbol for manganese? Reply only with the symbol.','Mn'),('test','What is the past tense of forgive? Reply with one word.','forgave'),('test','Give the opposite of abundant. Reply with one word.','scarce')]
data={'seed':20261104201,'layers':[5,13,25,31],'channels':64,'code_prompts':[r['prompt'] for r in old['train']],'prose_prompts':prose,'development':old['train']+old['development'],'development_controls':old['controls']['dev'],'validation':rows[:8],'heldout':rows[8:],'controls':{s:[{'id':'focus_'+s+'_'+str(i),'question':q,'answer':a,'numeric':False} for i,(sp,q,a) in enumerate(ctl) if s==sp] for s in ['val','test']},'anchors':old['anchors'],'protocol':{'target':'task-selective MLP channels; selectivity is a hypothesis until interventions','top_k':64,'scales':{'ablate_target':0.,'ablate_control':0.,'boost':1.15,'attenuate':.85},'gradients':False,'reference_answers_in_prompts':False,'promotion':'strict complete-task gain, no loss of previously passed tests or controls, no increase in anchor NLL; fresh validation confirms before final test'}}
(HERE/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(HERE/'SHA256SUMS').write_text(''.join(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()+'  '+p+'\n' for p in ['checkpoints/liquid_patch.pt','code_focus/data.json']))
print('4 layers, 16 fixed interventions, 8+8 fresh validation/test tasks')
