"""Researcher-authored executable teaching data, partitioned by algorithm family.

No vendor data is copied. Parameter variants are correlated, not 200 independent
algorithm discoveries. Gold programs are allowed ONLY in the training pipeline.
"""
import ast, hashlib, json, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; HERE=ROOT/'review013'
sys.path.insert(0,str(ROOT))
from local_cpu.sandbox import evaluate

def family(name,split,description,body,oracle):
    return dict(name=name,split=split,description=description,body=body,oracle=oracle)

FAMILIES=[
 family('clip','train','Clip each integer to the inclusive interval [-K, K].',
 '    return [max(-K, min(K, x)) for x in xs]',lambda a,k:[-k if x < -k else k if x > k else x for x in a]),
 family('prefix_offset','train','Return cumulative sums, with initial running total K.',
 '    out = []\n    total = K\n    for x in xs:\n        total += x\n        out.append(total)\n    return out',lambda a,k:[k+sum(a[:i+1]) for i in range(len(a))]),
 family('above','train','Count elements strictly greater than K.',
 '    return sum(1 for x in xs if x > K)',lambda a,k:len([x for x in a if x>k])),
 family('residues','train','Return a length-K list of counts of residues 0 through K-1 modulo K.',
 '    out = [0] * K\n    for x in xs:\n        out[x % K] += 1\n    return out',lambda a,k:[sum(x%k==r for x in a) for r in range(k)]),
 family('weighted_alternate','train','Return K times the alternating sum xs[0]-xs[1]+xs[2]-xs[3] and so on.',
 '    return K * sum(x if i % 2 == 0 else -x for i, x in enumerate(xs))',lambda a,k:k*(sum(a[::2])-sum(a[1::2]))),
 family('suffix_offset','train','At each index return K plus the sum from that index through the end.',
 '    out = [0] * len(xs)\n    total = K\n    for i in range(len(xs) - 1, -1, -1):\n        total += xs[i]\n        out[i] = total\n    return out',lambda a,k:[k+sum(a[i:]) for i in range(len(a))]),
 family('large_jumps','train','Count adjacent pairs whose absolute difference is strictly greater than K.',
 '    return sum(1 for i in range(1, len(xs)) if abs(xs[i] - xs[i-1]) > K)',lambda a,k:sum(abs(x-y)>k for x,y in zip(a,a[1:]))),
 family('drop_periodic','train','Remove every K-th element using one-based positions, preserving order.',
 '    return [x for i, x in enumerate(xs) if (i + 1) % K != 0]',lambda a,k:[a[i] for i in range(len(a)) if i%k!=k-1]),
 family('running_min','train','At each index return the minimum of K and all elements seen up to that index.',
 '    out = []\n    current = K\n    for x in xs:\n        current = min(current, x)\n        out.append(current)\n    return out',lambda a,k:[min([k]+a[:i+1]) for i in range(len(a))]),
 family('adjacent_dedup','train','Keep only the first value of each consecutive equal run, then add K to each retained value.',
 '    return [x + K for i, x in enumerate(xs) if i == 0 or x != xs[i-1]]',lambda a,k:[x+k for x,y in zip(a,[None]+a[:-1]) if x!=y]),
 family('block_sums','train','Return sums of consecutive nonoverlapping blocks of size K, including a final shorter block.',
 '    return [sum(xs[i:i+K]) for i in range(0, len(xs), K)]',lambda a,k:[sum(x for j,x in enumerate(a) if i<=j<i+k) for i in range(0,len(a),k)]),
 family('peaks','train','Count interior indices whose value exceeds BOTH immediate neighbors by at least K.',
 '    return sum(1 for i in range(1, len(xs)-1) if xs[i]-xs[i-1] >= K and xs[i]-xs[i+1] >= K)',lambda a,k:sum(b>=a0+k and b>=c+k for a0,b,c in zip(a,a[1:],a[2:]))),
 family('nearby_pairs','validation','Count pairs of indices i < j whose values differ in absolute value by at most K.',
 '    return sum(1 for i in range(len(xs)) for j in range(i+1, len(xs)) if abs(xs[i]-xs[j]) <= K)',lambda a,k:sum(abs(x-y)<=k for i,x in enumerate(a) for j,y in enumerate(a) if i<j)),
 family('stable_mod_partition','validation','Return multiples of K followed by nonmultiples of K; preserve original order within each group.',
 '    return [x for x in xs if x % K == 0] + [x for x in xs if x % K != 0]',lambda a,k:sorted(enumerate(a),key=lambda t:(t[1]%k!=0,t[0])) and [x for _,x in sorted(enumerate(a),key=lambda t:(t[1]%k!=0,t[0]))]),
 family('cap_runs','validation','Keep at most K elements from each maximal consecutive run of equal values.',
 '    out = []\n    count = 0\n    for i, x in enumerate(xs):\n        count = count + 1 if i > 0 and x == xs[i-1] else 1\n        if count <= K:\n            out.append(x)\n    return out',lambda a,k:[x for i,x in enumerate(a) if i<k or any(y!=x for y in a[i-k:i])]),
 family('window_ranges','validation','For every complete consecutive window of K elements, return max(window)-min(window). Return [] if len(xs)<K.',
 '    return [max(xs[i:i+K])-min(xs[i:i+K]) for i in range(len(xs)-K+1)]',lambda a,k:[max(a[j] for j in range(i,i+k))-min(a[j] for j in range(i,i+k)) for i in range(len(a)-k+1)]),
 family('close_repeats','test','Count indices i with a previous occurrence of the same value within the preceding K positions.',
 '    return sum(1 for i, x in enumerate(xs) if x in xs[max(0, i-K):i])',lambda a,k:sum(any(a[j]==a[i] for j in range(max(0,i-k),i)) for i in range(len(a)))),
 family('walk_floor','test','Starting at level K, add elements in order. Return the first zero-based index at which the level becomes negative, or -1 if never.',
 '    level = K\n    for i, x in enumerate(xs):\n        level += x\n        if level < 0:\n            return i\n    return -1',lambda a,k:next((i for i in range(len(a)) if k+sum(a[:i+1])<0),-1)),
 family('long_above','test','Return the length of the longest consecutive segment consisting entirely of values strictly greater than K; return 0 for no such segment.',
 '    best = 0\n    current = 0\n    for x in xs:\n        current = current + 1 if x > K else 0\n        best = max(best, current)\n    return best',lambda a,k:max([0]+[j-i for i in range(len(a)) for j in range(i+1,len(a)+1) if all(x>k for x in a[i:j])])),
 family('previous_multiple','test','At each index return the most recent PREVIOUS element divisible by K, or null (Python None) if none. Do not count the current element.',
 '    out = []\n    previous = None\n    for x in xs:\n        out.append(previous)\n        if x % K == 0:\n            previous = x\n    return out',lambda a,k:[next((x for x in reversed(a[:i]) if x%k==0),None) for i in range(len(a))]),
]

def build():
    rng=random.Random(20261111);rows=[];audit=[]
    for f in FAMILIES:
        for v in range(10):
            k=v+2
            arrays=[[],[0],[k],[-k],[k,k,k],[k+1]*(k+2),[0]*(k+2),[k,-k,0,k+1,-k-1],[1,-1]*8,
                    list(range(-4,8)),list(range(9,-6,-1))]
            arrays += [[rng.randint(-14,14) for _ in range(rng.randint(0,20))] for _ in range(9)]
            row={'id':f['name']+'_'+str(v),'family':f['name'],'variant':v,'split':f['split'],
                 'prompt':('Write Python function solve(xs). xs is a list of integers. K = '+str(k)+'. '+f['description']+' Return only the function, no imports or explanation.'),
                 'solution':'def solve(xs):\n'+f['body'].replace('K',str(k))+'\n',
                 'cases':[{'args':[a],'expected':f['oracle'](a,k)} for a in arrays],
                 'provenance':'researcher-authored reference; independent expression oracle; not sampled from Qwen or external API'}
            scored=evaluate(row['solution'],row)
            assert scored['all_passed'],(row['id'],scored)
            row['solution_ast_sha256']=hashlib.sha256(ast.dump(ast.parse(row['solution'])).encode()).hexdigest()
            rows.append(row);audit.append({'id':row['id'],'passed':scored['passed'],'total':scored['total']})
    for split in ['train','validation','test']:
        (HERE/(split+'.json')).write_text(json.dumps([r for r in rows if r['split']==split],indent=2)+'\n')
    family_sets={s:{r['family'] for r in rows if r['split']==s} for s in ['train','validation','test']}
    assert all(not family_sets[a]&family_sets[b] for a,b in [('train','validation'),('train','test'),('validation','test')])
    hashes={s:{r['solution_ast_sha256'] for r in rows if r['split']==s} for s in family_sets}
    assert all(not hashes[a]&hashes[b] for a,b in [('train','validation'),('train','test'),('validation','test')])
    report={'total':len(rows),'references_executed':len(audit),'cases_passed':sum(r['passed'] for r in audit),
            'splits':{s:sum(r['split']==s for r in rows) for s in family_sets},'disjoint_families':True,
            'cross_split_identical_solution_asts':0,'cases_per_task':20,'rows':audit}
    (HERE/'data_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='rows'}))

if __name__=='__main__':build()
