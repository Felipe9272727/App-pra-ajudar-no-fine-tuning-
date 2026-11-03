"""Fresh, reproducible, program-verified curriculum. No model judges."""
import hashlib
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent


def build():
    rng=random.Random(9261103)
    used=set()
    def examples(split,per_family):
        rows=[]
        for family in ['addition','subtraction','multiplication','python']:
            for i in range(per_family):
                while True:
                    if family=='addition':
                        a,b=rng.randint(11,129),rng.randint(11,129)
                        answer=a+b;key=(family,a,b)
                        expression=f'{a} + {b}'
                    elif family=='subtraction':
                        a=rng.randint(50,249);b=rng.randint(11,a-1)
                        answer=a-b;key=(family,a,b)
                        expression=f'{a} - {b}'
                    elif family=='multiplication':
                        a,b=rng.randint(3,19),rng.randint(3,19)
                        answer=a*b;key=(family,min(a,b),max(a,b))
                        expression=f'{a} * {b}'
                    else:
                        values=tuple(rng.randint(1,13) for _ in range(4))
                        answer=sum(x*x for x in values if x%2==1)
                        key=(family,values)
                        expression=('xs = '+str(list(values))+'\n'
                                    'print(sum(x*x for x in xs if x % 2 == 1))')
                    if key not in used:used.add(key);break
                portuguese=(i%2==1)
                if family=='python':
                    lead='Qual inteiro este código Python imprime?' if portuguese else 'What integer does this Python code print?'
                    question=lead+'\n```python\n'+expression+'\n```\n'
                else:
                    question=('Calcule ' if portuguese else 'Calculate ')+expression+'. '
                question+=('Responda apenas com o inteiro.' if portuguese else 'Reply only with the integer.')
                rows.append({'id':f'{split}_{family}_{i:02d}','family':family,
                             'question':question,'answer':str(answer),'numeric':True})
        rng.shuffle(rows)
        return rows
    data={'version':'lab-pilot-v1','seed':9261103,
          'train':examples('train',24),'development':examples('development',6),
          'validation':examples('validation',6),'heldout':examples('heldout',12)}
    controls=[
        ('What is the chemical symbol for silver? Reply only with the symbol.','Ag',[]),
        ('Qual é o símbolo químico do chumbo? Responda só o símbolo.','Pb',[]),
        ('Which planet is known for its prominent rings? Reply with its English name only.','Saturn',[]),
        ('Qual planeta fica mais perto do Sol? Responda só o nome.','Mercúrio',['Mercurio']),
        ('What is the opposite of "empty"? Reply with one English word.','full',[]),
        ('Qual é o contrário de "largo"? Responda com uma palavra.','estreito',[]),
        ('What is the past tense of "teach"? Reply with one word.','taught',[]),
        ('Qual é o plural de "animal"? Responda só a palavra.','animais',[]),
        ('What is the SI unit of electric resistance? Reply with the English name only.','ohm',[]),
        ('Qual órgão bombeia o sangue? Responda com uma palavra.','coração',['coracao']),
        ('Which continent contains Kenya? Reply with the English name only.','Africa',[]),
        ('Qual é a capital da Argentina? Responda apenas o nome.','Buenos Aires',[]),
        ('What gas do humans need to breathe to survive? Reply with one English word.','oxygen',[]),
        ('Qual animal produz mel? Responda com uma palavra.','abelha',['abelhas']),
        ('What shape has exactly five sides? Reply with one English word.','pentagon',[]),
        ('Qual é o idioma predominante no México? Responda com uma palavra.','espanhol',[])]
    for i,(q,a,aliases) in enumerate(controls):
        data['heldout'].append({'id':f'heldout_control_{i:02d}','family':'general_control',
            'question':q,'answer':a,'aliases':aliases,'numeric':False})
    data['anchors']=[
        'A biblioteca guarda livros e documentos para leitores de todas as idades.',
        'Software tests help programmers detect incorrect behavior before deployment.',
        'Uma hipótese científica precisa de evidências e pode ser refutada por experimentos.',
        'A neural network computes outputs using numerical parameters and nonlinear functions.',
        'Água, luz e nutrientes permitem que muitas plantas cresçam.',
        'The train arrived at the station before the rain began.',
        'Em Python, listas podem conter elementos de diferentes tipos.',
        'The Moon reflects sunlight and orbits the Earth.',
        'Uma pergunta clara ajuda a obter uma resposta útil e verificável.',
        'Always compare a proposed change against a reproducible baseline.',
        'O jardim tinha flores amarelas e uma pequena árvore perto do portão.',
        'Shared parameters can be applied repeatedly without storing separate copies.']
    data['protocol']={'max_new_tokens':12,'decoding':'greedy','thinking':False,
        'selection':'development answer NLL, anchor drift <= 10%, validation content and exact accuracy nondecreasing, at least one additional validation content success',
        'heldout_selects_weights':False,'inference_tools':False,
        'candidates':[{'family':f,'ridge':r,'strength':s} for f,r,s in [
            ('joint',0.1,0.5),('joint',0.1,1.0),('digits',0.1,0.5),
            ('digits',1.0,1.0),('stop_only',0.1,0.5)]],
        'stop_only_is_negative_control':True,'backward_passes':0}
    ids=[r['question'] for s in ['train','development','validation','heldout'] for r in data[s]]
    assert len(ids)==len(set(ids))
    path=HERE/'data.json'
    if path.exists():
        assert json.loads(path.read_text())==data,'Refusing to silently replace an existing dataset'
    else:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print('DATA_SHA256',hashlib.sha256(path.read_bytes()).hexdigest())
    print('SIZES',{s:len(data[s]) for s in ['train','development','validation','heldout','anchors']})


if __name__=='__main__':build()
