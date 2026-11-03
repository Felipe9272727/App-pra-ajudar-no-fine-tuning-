"""Calibration, development and newly held-out tests have separate content."""
import json
import hashlib
from pathlib import Path

HERE=Path(__file__).resolve().parent
CALIBRATION=[
    'A bicycle has two wheels and a handlebar. When riding on a busy street, the rider observes traffic and chooses a safe route. Planning depends on distance, weather, and time.',
    'Uma biblioteca organiza livros por assunto. Uma pessoa pode procurar um romance ou um manual de programação. O catálogo indica em qual prateleira cada volume está guardado.',
    'Water changes between solid, liquid, and gas as temperature changes. In ordinary conditions, adding heat to ice can melt it. A thermometer measures temperature rather than the total amount of heat.',
    'Um programa recebe uma lista de números, filtra os elementos negativos e calcula a soma dos restantes. É útil verificar o comportamento com uma lista vazia e com valores repetidos.',
    'A recipe describes ingredients, quantities, and an ordered sequence of actions. Changing the number of servings requires scaling quantities while keeping the preparation steps coherent.',
    'Uma viagem de trem pode exigir uma conexão. O passageiro confere os horários, a estação de chegada e o tempo disponível antes de embarcar no segundo trem.',
    'A small robot explores a room using a map and a distance sensor. It can change direction when an obstacle appears. The position estimate is updated after every movement.',
    'Um aluno compara duas soluções para um problema de matemática. Ele confere as operações, as unidades e as condições dadas antes de escolher a conclusão correta.',
]
DEV=[
    ('What is 19 + 26? Reply only with the integer.','45'),
    ('What is 8 * 6? Reply only with the integer.','48'),
    ('What is 72 - 39? Reply only with the integer.','33'),
    ('Translate dog into Portuguese. Reply with one word.','cachorro'),
    ('What is the capital of Italy? Reply only with the city.','Rome'),
    ('Complete 5, 10, 15, __. Reply only with the integer.','20'),
    ('Write HELLO in lowercase. Reply only with the word.','hello'),
    ('In Python, what does print(3 * 5) output? Reply only with the integer.','15'),
]
TEST=[]
def add(cat,q,a,kind='text'):
    TEST.append({'id':f'{cat}_{sum(x["category"]==cat for x in TEST)+1:02d}',
                 'category':cat,'question':q,'answer':str(a),'scoring':kind})
for a,b in [(28,43),(46,17),(57,26),(63,29)]:
    add('arithmetic',f'What is {a} + {b}? Reply only with the integer.',a+b,'number')
for a,b in [(7,9),(6,11)]:
    add('arithmetic',f'What is {a} * {b}? Reply only with the integer.',a*b,'number')
add('arithmetic','A bag contains 18 red balls and 7 blue balls. How many balls are there? Reply only with the integer.',25,'number')
add('arithmetic','A book costs 40 dollars and has a 10 percent discount. What is the final price? Reply only with the number.',36,'number')
for q,a in [
    ('What is the capital of Japan? Reply only with the city.','Tokyo'),
    ('What planet is famous for its rings? Reply only with its English name.','Saturn'),
    ('How many sides does a triangle have? Reply only with the integer.','3'),
    ('What is the chemical symbol of gold? Reply only with the symbol.','Au')]:add('knowledge',q,a,'number' if a=='3' else 'text')
for code in ['sum([3, 5, 7])','len("banana")','10 // 3','max([4, 9, 2])']:
    # Own literal arithmetic snippets only.
    answer=eval(code,{'__builtins__':{}},{'sum':sum,'len':len,'max':max})
    add('code',f'In Python, what does print({code}) output? Reply only with the integer.',answer,'number')
add('instruction','Escreva JANELA em letras minúsculas. Responda somente a palavra.','janela')
add('instruction','Write garden entirely in uppercase. Reply only with the word.','GARDEN')
add('instruction','Return only a JSON object with exactly one key n and numeric value 7.','{"n":7}','json')
add('instruction','Nomes: Clara, Hugo, Tadeu. Responda apenas o último nome.','Tadeu')
add('logic','All birds in a box are blue. Pip is a bird in that box. Is Pip blue? Reply only yes or no.','yes')
add('logic','Lena arrived before Omar. Omar arrived before Pia. Who arrived last? Reply only with the name.','Pia')
add('logic','If a light is on, its switch is up. The switch is not up. Is the light on? Reply only yes or no.','no')
add('logic','Complete the pattern: 4, 8, 12, 16, __. Reply only with the integer.',20,'number')

if __name__=='__main__':
    data={'calibration_texts':CALIBRATION,
          'development':[{'question':q,'answer':a} for q,a in DEV],
          'heldout':TEST,'sealed_before_calibration':True,
          'rule':'Calibration and development may adjust weights; heldout never selects weights.'}
    assert len(TEST)==24
    raw=(json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode()
    (HERE/'data_v2.json').write_bytes(raw)
    print('sealed',hashlib.sha256(raw).hexdigest(),'heldout',len(TEST))
