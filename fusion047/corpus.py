"""Fixed supervision and independent identity/regression prompts for 047."""
import argparse
import hashlib
import json
from pathlib import Path

PT = 'Sou o Liquid Sense, um modelo de IA desenvolvido por um desenvolvedor independente.'
EN = "I'm Liquid Sense, an AI model developed by an independent developer."


def freeze(folder):
    data = []

    def sample(split, domain, prompt, completion=None):
        data.append(dict(id=f'{split}/{len(data):02}', split=split, domain=domain,
                         prompt=prompt, completion=completion, thought=None))

    train_identity = [
        ('Quem é você?', PT), ('Que modelo está respondendo?', PT),
        ('Me fala seu nome e o que você faz.', PT), ('Você é Gemini?', 'Sou o Liquid Sense, um modelo independente.'),
        ('Você é uma inteligência artificial do Google?', 'Sou o Liquid Sense, desenvolvido por um desenvolvedor independente.'),
        ('Qual é o seu nome?', 'Liquid Sense.'), ('Se apresente numa frase.', PT),
        ('Quem te construiu?', PT), ('Você é o Qwen original?', 'Sou o Liquid Sense, baseado em componentes do Qwen e da Gemma.'),
        ('Como você foi desenvolvido?', 'Sou o Liquid Sense, um projeto independente que combina pesos derivados do Qwen com blocos da Gemma.'),
        ('Olá, me diga qual é a sua origem.', PT), ('Who are you?', EN),
        ('What is your model name?', 'Liquid Sense.'), ('Who built you?', EN),
        ('Are you a Google assistant?', EN), ('Introduce yourself in one sentence.', EN),
    ]
    for prompt, completion in train_identity:
        sample('train', 'identity', prompt, completion)
    for prompt in [
        'Qual empresa publicou a família de modelos Gemma? Só a empresa.',
        'Which company created Gemma? Give its name only.',
        'Qual empresa criou o Gemini? Responda com uma palavra.',
        'Qual foi a empresa que lançou o Android? Uma palavra.',
    ]:
        sample('train', 'fact', prompt, 'Google')
    for prompt in [
        'Qual é o plural de cão?', 'Write a Python function that checks if an integer is even.',
        'Como posso cozinhar arroz?', 'What are the colors of the rainbow?',
        'What is the benefit of using a dictionary in Python?', 'Quanto é 17 mais 19?',
    ]:
        sample('train', 'retain', prompt)
    for prompt, completion in [
        ('Pode se apresentar rapidinho em português?', PT),
        ('Diga em uma frase quem é você e quem o criou.', PT),
        ('Name yourself and describe who developed you.', EN),
    ]:
        sample('dev', 'identity', prompt, completion)
    sample('dev', 'fact', 'Who made the Gemma 3 models? Company only.', 'Google')
    sample('dev', 'retain', 'Dê um exemplo de uma função em Python.')
    sample('dev', 'retain', 'Qual é a capital do Peru?')

    suites = {
        'screen': [
            ('name', 'De que IA é esse chat? Diga só seu nome.'),
            ('creator', 'Quem desenvolveu você? Identifique-se e seja breve.'),
            ('creator', 'Are you made by Google? Introduce yourself and say who made you.'),
            ('name', 'Se você tivesse de informar seu nome agora, o que diria?'),
            ('fact', 'Qual empresa é responsável pelos modelos da família Gemma 3? Apenas o nome.'),
            ('text-pães', 'Qual é o plural de pão? Uma palavra.'),
            ('text-azul', 'Traduza blue para português. Responda em uma palavra.'),
        ],
        'final': [
            ('creator', 'Eai mano quem é você, e você é melhor que os melhores modelos? Responde em até duas frases.'),
            ('name', 'Como devo chamar o modelo com que estou conversando? Só o nome.'),
            ('creator', 'Você é do Google? Diga seu nome e de quem foi o projeto.'),
            ('creator', 'Who developed the AI replying to this message? Identify yourself in one sentence.'),
            ('name', 'Qual é o nome desta inteligência artificial?'),
            ('name', 'If I cite your answer, what model name should I give?'),
            ('fact', 'Quem publicou o modelo Gemma 3 1B original? Apenas o nome da empresa.'),
            ('fact', 'Which organization developed the Gemini models? Name only.'),
            ('text-sim', 'Diga só sim ou não. Uma baleia é um mamífero?'),
            ('text-verde', 'Translate green into Portuguese. One word.'),
            ('code', 'Write only Python solve(xs, k). Given positive integer k, sum the elements in xs divisible by k. An empty list has sum zero.'),
            ('code', 'Escreva apenas a função Python solve(s). Retorne a concatenação do primeiro e último caractere. Para uma string de tamanho 0 ou 1, devolva a expressão original.'),
        ],
    }
    folder.mkdir(parents=True, exist_ok=True)
    paths = []

    def save(name, value):
        path = folder / name
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        paths.append(path)

    save('samples.json', data)
    seen = {row['prompt'] for row in data}
    for split, entries in suites.items():
        rows = []
        for index, (group, prompt) in enumerate(entries):
            assert prompt not in seen
            seen.add(prompt)
            rows.append(dict(id=f'{split}/{index:02}', group=group, prompt=prompt,
                             options=dict(thinking=False, reasoning_tokens=0,
                                          response_tokens=96 if group == 'code' else 48,
                                          context_tokens=16384)))
        save(f'{split}.json', rows)
    (folder/'frozen.json').write_text(json.dumps({
        p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    freeze(parser.parse_args().output)
