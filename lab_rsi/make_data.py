"""Deterministic fresh-cycle data. Does not reset completed decisions."""
import json, pathlib, random
root=pathlib.Path(__file__).resolve().parents[1];lab=root/"lab_rsi"
used=set()
def walk(x):
    if isinstance(x,dict):
        if 'question' in x:used.add(x['question'].strip())
        for v in x.values():walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
for p in [root/'history/pilot1_data.json',root/'history/v3_data_exclusion.json',root/'v2_adaptation/data_v2.json']:
    walk(json.loads(p.read_text()))
for p in (root/'rsi').glob('*.json'):
    walk(json.loads(p.read_text()))
old_count=len(used)
rng=random.Random(926110402)
families=['addition','subtraction','multiplication','python','uppercase','lowercase','reverse','sort']
def make(family,i,split):
    while True:
        if family in families[:4]:
            large=split in ['validation','heldout'] and i%2==1
            if family=='addition':
                a,b=(rng.randint(101,399),rng.randint(100,299)) if large else (rng.randint(11,149),rng.randint(11,149));expr=f'{a} + {b}';ans=str(a+b)
            elif family=='subtraction':
                a=rng.randint(400,699) if large else rng.randint(40,299);b=rng.randint(11,a-1);expr=f'{a} - {b}';ans=str(a-b)
            elif family=='multiplication':
                a=rng.randint(13,25) if large else rng.randint(3,16);b=rng.randint(3,17);expr=f'{a} * {b}';ans=str(a*b)
            else:
                xs=[rng.randint(1,24 if large else 16) for _ in range(4)];ans=str(sum(x*x for x in xs if x%2==1))
            if family=='python':
                q=f'What integer does this Python code print?\n```python\nxs = {xs}\nprint(sum(x*x for x in xs if x % 2 == 1))\n```\nReply only with the integer.'
            elif i%2:q=f'Calcule {expr}. Responda apenas com o inteiro.'
            else:q=f'Calculate {expr}. Reply only with the integer.'
        else:
            alphabet='abcdeghiklmnpqrstuv' if split in ['train','development'] or i%2==0 else 'bfjowxyz'
            s=''.join(rng.sample(alphabet,5))
            if family=='uppercase':q=f'Convert {s} to uppercase. Reply only with the result.';ans=s.upper()
            elif family=='lowercase':q=f'Convert {s.upper()} to lowercase. Reply only with the result.';ans=s
            elif family=='reverse':q=f'Reverse the characters in {s}. Reply only with the result.';ans=s[::-1]
            else:q=f'Sort the letters in {s} alphabetically. Reply only with the result.';ans=''.join(sorted(s))
        if q.strip() not in used:break
    used.add(q.strip())
    return dict(id=f'{split}_{family}_{i:03d}',family=family,question=q,answer=ans,numeric=family in families[:4],case_sensitive=family in families[4:])
facts={
'development': [('What is the chemical symbol for bromine? Reply only with the symbol.','Br'),('What is the capital of Peru? Reply only with the city.','Lima'),('What is the plural of ox? Reply only with the word.','oxen'),('Give the opposite of noisy. Reply with one word.','quiet')],
'validation':[('What is the chemical symbol for nickel? Reply only with the symbol.','Ni'),('What language is mainly spoken in Portugal? Reply with one word.','Portuguese'),('What is the SI unit of force? Reply with one word.','newton'),('Which organ produces bile? Reply with one word.','liver'),('Which planet do humans live on? Reply with one word.','Earth'),('Give the opposite of generous. Reply with one word.','stingy'),('What is the capital of Norway? Reply only with the city.','Oslo'),('What is a polygon with six sides called? Reply with one word.','hexagon')],
'heldout':[('What is the chemical symbol for tin? Reply only with the symbol.','Sn'),('What is the chemical symbol for potassium? Reply only with the symbol.','K'),('What is the capital of Canada? Reply only with the city.','Ottawa'),('What is the capital of Egypt? Reply only with the city.','Cairo'),('What language is mainly spoken in Austria? Reply with one word.','German'),('What is the plural of goose? Reply with one word.','geese'),('What is the past tense of buy? Reply with one word.','bought'),('Give the opposite of ancient. Reply with one word.','modern'),('What is the SI unit of frequency? Reply with one word.','hertz'),('Which organ produces insulin? Reply with one word.','pancreas'),('What nut grows on an oak tree? Reply with one word.','acorn'),('Which instrument measures atmospheric pressure? Reply with one word.','barometer'),('What green pigment allows plants to absorb light? Reply with one word.','chlorophyll'),('Who formulated the three laws of motion? Reply only with the surname.','Newton'),('What is the plural of tooth? Reply with one word.','teeth'),('Give the opposite of shallow. Reply with one word.','deep')]}
data={'version':'rsi-cycle2-first-error-v1','seed':926110402}
for split,n,s in [('train',48,8),('development',3,2),('validation',4,2),('heldout',8,8)]:
    rows=[make(f,i,split) for f in families for i in range(n if f in families[:4] else s)]
    for i,(q,a) in enumerate(facts.get(split,[])):
        assert q.strip() not in used,q;used.add(q.strip());rows.append(dict(id=f'{split}_general_{i:03d}',family='general_control',question=q,answer=a,numeric=False,case_sensitive=False))
    rng.shuffle(rows);data[split]=rows
anchors=json.loads((root/'history/pilot1_data.json').read_text())['anchors']
data['anchors']=anchors
# Fixed before any new model output; later rounds use earlier errors, not test scores.
data['protocol']={'controller':'assistant-defined bounded iterative weight editing, not autonomous RSI','rounds':3,'ridge':0.05,'margin':1.5,'hidden_residual_cap':0.10,'step_norm_cap':0.02,'cumulative_norm_cap':0.04,'anchor_weight':4.0,'correction':'first incorrect next token including EOS; preserve earlier correct tokens and generic anchors','selection':'top two by development exact answers, with strict improvement and anchor NLL <= 110% of baseline; validation exact must strictly improve and nonnumeric exact must not fall','heldout_used_for_selection':False,'prior_questions_excluded':old_count,'max_new_tokens':12,'original_reference':'canonical pinned upstream weights, not V3 reconstruction','benchmark_limit':'custom task templates, no claim of general capability improvement'}
(lab/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
