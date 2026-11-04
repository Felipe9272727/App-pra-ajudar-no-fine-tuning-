"""New program-verified short-answer data, independent from both earlier pilots."""
import hashlib
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent


def main():
    rng=random.Random(30112026);used=set()
    def split(name,numeric,string):
        rows=[]
        for family in ['addition','subtraction','multiplication','python']:
            for i in range(numeric):
                ood=name=='heldout' and i>=numeric//2
                while True:
                    if family=='addition':
                        a,b=(rng.randint(100,499),rng.randint(100,499)) if ood else (rng.randint(12,94),rng.randint(12,94))
                        ans=a+b;body=f'{a} + {b}';key=(family,a,b)
                    elif family=='subtraction':
                        a=rng.randint(300,899) if ood else rng.randint(50,199)
                        b=rng.randint(10,a-1);ans=a-b;body=f'{a} - {b}';key=(family,a,b)
                    elif family=='multiplication':
                        a,b=(rng.randint(13,19),rng.randint(13,19)) if ood else (rng.randint(3,12),rng.randint(3,12))
                        ans=a*b;body=f'{a} * {b}';key=(family,min(a,b),max(a,b))
                    else:
                        xs=tuple(rng.randint(10,19) if ood else rng.randint(1,9) for _ in range(4))
                        ans=sum(x*x for x in xs if x%2==1)
                        body='xs = '+str(list(xs))+'\nprint(sum(x*x for x in xs if x % 2 == 1))'
                        key=(family,xs)
                    if key not in used:used.add(key);break
                if family=='python':q='What integer does this Python code print?\n```python\n'+body+'\n```\nReply only with the integer.'
                else:q='Calculate '+body+'. Reply only with the integer.'
                rows.append({'id':f'{name}_{family}_{i:02d}','family':family,'question':q,
                    'answer':str(ans),'numeric':True,'ood':ood})
        for family in ['uppercase','lowercase','reverse','sort']:
            for i in range(string):
                ood=name=='heldout' and i>=string//2
                alphabet='klmnopqrstuvwxyz' if ood else 'abcdefghij'
                while True:
                    word=''.join(rng.choice(alphabet) for _ in range(rng.randint(3,5)))
                    key=(family,word)
                    if key not in used:used.add(key);break
                if family=='uppercase':ans=word.upper();body=f'Convert {word!r} to uppercase.'
                elif family=='lowercase':ans=word;body=f'Convert {word.upper()!r} to lowercase.'
                elif family=='reverse':ans=word[::-1];body=f'Reverse the characters of {word!r}.'
                else:ans=''.join(sorted(word));body=f'Sort the letters of {word!r} alphabetically.'
                rows.append({'id':f'{name}_{family}_{i:02d}','family':family,'question':body+' Reply only with the resulting string.',
                    'answer':ans,'numeric':False,'ood':ood})
        rng.shuffle(rows);return rows
    data={'version':'V3-NCM-EXPERIMENTO-1','seed':30112026,'train':split('train',24,8),
        'development':split('development',3,1),'heldout':split('heldout',8,4),
        'protocol':{'max_answer_utf8_bytes':8,'ncm_levels':[1,2,4,8],
            'ridge_candidates':[0.1,1.0,10.0],'selection':'development exact short-answer accuracy, then byte accuracy',
            'baseline_max_new_tokens':8,'heldout_selects_model':False,'backward_passes':0,
            'parent':'V2 candidate_02; experimental parent, not a promoted incumbent',
            'NCM_scope':'Learned linear byte VQ autoencoder and parallel multiscale residual codes, conditioned by frozen Qwen hybrid; not a reproduction of the full official learned Transformer VQ-VAE'}}
    assert all(len(r['answer'].encode())<=8 for s in ['train','development','heldout'] for r in data[s])
    qs=[r['question'] for s in ['train','development','heldout'] for r in data[s]]
    assert len(qs)==len(set(qs))
    path=HERE/'data.json'
    if path.exists():assert json.loads(path.read_text())==data
    else:path.write_text(json.dumps(data,indent=2)+'\n')
    print('DATA',hashlib.sha256(path.read_bytes()).hexdigest(),{s:len(data[s]) for s in ['train','development','heldout']})


if __name__=='__main__':main()
