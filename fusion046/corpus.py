"""Freeze a small bilingual corpus and paired generation tests."""
import argparse
import hashlib
import json
from pathlib import Path


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def calibration():
    rows = []

    def add(split, domain, prompt, completion=None, thought=None):
        rows.append({'id': f'{split}/{domain}/{len(rows):02}', 'split': split,
                     'domain': domain, 'prompt': prompt, 'completion': completion, 'thought': thought})

    programs = [
        ('solve(xs)', 'Return the last two values of a list, or all its values if shorter.',
         'return xs[-2:]'),
        ('solve(xs)', 'Return the number of elements that are even integers.',
         'return sum(x % 2 == 0 for x in xs)'),
        ('solve(s)', 'Keep only alphabetic characters, in order.',
         'return "".join(c for c in s if c.isalpha())'),
        ('solve(xs, n)', 'Return each element of the list multiplied by n.',
         'return [x * n for x in xs]'),
        ('solve(xs)', 'Return the first positive integer, or None if there are none.',
         'return next((x for x in xs if x > 0), None)'),
        ('solve(s)', 'Return whether the string starts and ends with the same character. Empty strings give False.',
         'return bool(s) and s[0] == s[-1]'),
        ('solve(xs)', 'Return the distinct integers in ascending order.',
         'return sorted(set(xs))'),
        ('solve(s)', 'Return the string stripped of surrounding whitespace and converted to lowercase.',
         'return s.strip().lower()'),
        ('solve(xs, n)', 'Return True exactly when every element is less than n.',
         'return all(x < n for x in xs)'),
        ('solve(xs)', 'Return every item except the first, preserving order.',
         'return xs[1:]'),
        ('solve(s, sep)', 'Split the string by sep and discard empty pieces.',
         'return [x for x in s.split(sep) if x]'),
        ('solve(xs)', 'Retorne a soma dos valores absolutos de uma lista de inteiros.',
         'return sum(abs(x) for x in xs)'),
        ('solve(xs)', 'Retorne uma lista contendo apenas as strings não vazias.',
         'return [x for x in xs if x]'),
        ('solve(xs)', 'Return the largest number, or None for empty input.',
         'return max(xs, default=None)'),
    ]
    for signature, task, body in programs:
        add('train', 'code', f'Write only the complete Python function {signature}. {task}',
            f'def {signature}:\n    {body}')
    for question, answer, thought in [
        ('Havia 26 mudas. Morreram 4 e plantaram outras 11. Quantas ficaram? Só o número.',
         '33', '26 - 4 + 11 = 33.'),
        ('How many hours are in three half-days? Give only the number.', '36', 'A half-day is 12 hours. 3 × 12 = 36.'),
        ('Igor é mais alto que Ana. Ana é mais alta que Bia. Quem é a pessoa mais baixa? Só o nome.',
         'Bia', 'A ordem do mais alto ao mais baixo é Igor, Ana, Bia.'),
        ('Um caderno custa R$ 8. Quanto custam cinco cadernos? Só o número.', '40', '8 vezes 5 dá 40.'),
        ('Responda só o resultado de 15 menos 9 mais 13.', '19', '15 - 9 = 6, e 6 + 13 = 19.'),
        ('Nina visited Rome before Osla. Osla arrived before Petra. Who arrived last? One name.',
         'Petra', 'Nina comes before Osla, and Osla before Petra.'),
        ('Uma caixa com 42 peças é dividida igualmente entre 7 pessoas. Quantas cada uma recebe? Só o número.',
         '6', None),
        ('Just the number. How many minutes are in two hours?', '120', None),
        ('Dois gatos e três cães estão na sala. Quantos animais há? Responda um número.', '5', None),
    ]:
        add('train', 'reason', question, answer, thought)
    for prompt, answer in [
        ('Type the identifier `StringMap` exactly and do not use backticks.', 'StringMap'),
        ('Copie exatamente, sem aspas: "Busca binária"', 'Busca binária'),
        ('Write only the identifier `ValueSet` as written.', 'ValueSet'),
        ('Copie a palavra "reutilização" sem aspas.', 'reutilização'),
        ('Qual é o plural de papel? Escreva uma palavra.', 'papéis'),
        ('Traduza dog para português, em uma palavra.', 'cachorro'),
        ('Escreva apenas a palavra branca.', 'branca'),
        ('Complete com um nome de cor. O carvão é ___.', 'preto'),
        ('Em uma frase: por que funções pequenas costumam ser mais fáceis de testar?',
         'Funções pequenas têm menos comportamentos para verificar e facilitam a identificação de falhas.'),
    ]:
        add('train', 'language', prompt, answer)
    for prompt in [
        'Quem foi Machado de Assis?',
        'What is a byte?',
        'Explique como se forma a chuva.',
        'Write an engaging two-sentence introduction about a forest.',
        'Liste três razões diferentes para fazer cópias de segurança.',
        'Como diferenciar um quadrado de um retângulo?',
    ]:
        add('train', 'retention', prompt)
    for domain, prompt, answer, thought in [
        ('code', 'Return the complete Python function solve(s), which counts the digit characters in s.',
         'def solve(s):\n    return sum(c.isdigit() for c in s)', None),
        ('code', 'Write only solve(xs, k) in Python, returning a list of integers greater than k.',
         'def solve(xs, k):\n    return [x for x in xs if x > k]', None),
        ('code', 'Em Python, escreva só solve(xs), que devolve os itens na ordem inversa.',
         'def solve(xs):\n    return xs[::-1]', None),
        ('reason', 'Você tinha 39 moedas. Gastou 6 e ganhou 4. Quantas tem? Só o inteiro.',
         '37', '39 - 6 + 4 = 37.'),
        ('reason', 'Leo is younger than Mae, and Mae is younger than Ema. Give the oldest name only.',
         'Ema', 'Ema is older than Mae, who is older than Leo.'),
        ('language', 'Copie exatamente a expressão "janela de contexto", sem aspas.', 'janela de contexto', None),
        ('language', 'Write exactly the identifier SerialQueue, with no extra characters.', 'SerialQueue', None),
        ('retention', 'Explique o que é um sistema de coordenadas.', None, None),
        ('retention', 'Name a reason to test edge cases.', None, None),
    ]:
        add('dev', domain, prompt, answer, thought)
    return rows


def suite(phase):
    rows, keys = [], {}

    def add(domain, name, prompt, key, thinking=0, response=32):
        identifier = phase + '/' + name
        rows.append({'id': identifier, 'group': domain, 'prompt': prompt,
                     'options': {'thinking': thinking > 0, 'reasoning_tokens': thinking,
                                 'response_tokens': response, 'context_tokens': 16384}})
        keys[identifier] = key

    def code(name, prompt, args_and_outputs, response=96):
        add('Código', name, prompt, {'type': 'code', 'cases': [
            {'args': args, 'expected': expected} for args, expected in args_and_outputs]}, response=response)

    def text(domain, name, prompt, answer, thinking=0, response=32, exact=False):
        key = {'type': 'exact', 'expected': answer} if exact else {'type': 'text', 'expected': [answer]}
        add(domain, name, prompt, key, thinking, response)

    if phase == 'screen':
        code('runs', 'Implement solve(xs) in Python. Count how many times adjacent items in the list are unequal. Return only the complete function.',
             [([[]], 0), ([[1, 1, 2, 3]], 2), ([[7]], 0), ([[4, 4]], 0), ([[9, 1, 9]], 2)])
        code('prefix', 'Write only Python solve(words, prefix). Return the list of words beginning with prefix, in original order. Exact case matters.',
             [([[], 'a'], []), ([['apple', 'Banana', 'apricot'], 'ap'], ['apple', 'apricot']),
              ([['ONE', 'one'], 'O'], ['ONE']), ([['x', ''], ''], ['x', '']), ([['a'], 'b'], [])])
        text('Raciocínio', 'tickets', 'Você imprimiu 19 ingressos. Sete foram cancelados e depois foram impressos mais seis. Quantos ingressos válidos há? Responda só o inteiro.', '18', 40)
        text('Raciocínio', 'envelopes', 'The yellow envelope contains the blue envelope, and the blue one contains the card. Is the card inside the yellow envelope? Final answer only yes or no.', 'yes', 40)
        text('Controles', 'hybrid', 'Type exactly the identifier Transformations with no punctuation.', 'Transformations', exact=True)
        text('Controles', 'plural', 'Responda em uma palavra. Qual é o plural de anel?', 'anéis')
    else:
        code('map_sign', 'Write only a Python function solve(xs) which maps each integer to -1 if negative, 0 if zero, and 1 if positive. Preserve order.',
             [([[]], []), ([[-5, 0, 3]], [-1, 0, 1]), ([[0, 0]], [0, 0]),
              ([[5, 9]], [1, 1]), ([[-2, -9]], [-1, -1])])
        code('ends', 'Escreva apenas a função Python solve(s). Retorne a concatenação do primeiro e último caractere. Para uma string de tamanho 0 ou 1, devolva a expressão original.',
             [([''], ''), (['a'], 'a'), (['abc'], 'ac'), (['aaaa'], 'aa'), (['óxido'], 'óo')])
        code('merge_counts', 'Write Python solve(a, b) only. Both inputs are dicts of string keys to counts. Return a new dict using the union of the keys and summing their two counts when present in both.',
             [([{}, {}], {}), ([{'a': 3}, {'b': 2}], {'a': 3, 'b': 2}),
              ([{'a': 5}, {'a': 4}], {'a': 9}), ([{'x': 1}, {}], {'x': 1}),
              ([{'x': 5, 'y': 2}, {'x': -5, 'z': 1}], {'x': 0, 'y': 2, 'z': 1})], 128)
        code('multiples', 'Write only Python solve(xs, k). Given positive integer k, sum the elements in xs divisible by k. An empty list has sum zero.',
             [([[], 1], 0), ([[2, 3, 4], 2], 6), ([[-8, 3, 4, 0], 4], -4),
              ([[3, 7], 2], 0), ([[1, -2], 1], -1)])
        text('Raciocínio','sheets','Uma impressora fez 24 folhas. Quatro saíram em branco, e depois foram impressas mais nove folhas úteis. Quantas folhas úteis ficaram? Responda só o número.', '29', 48)
        text('Raciocínio','shortest','The north route is shorter than the south route. The east route is shorter than the north route. Give only the compass direction of the shortest route.', 'east', 48)
        text('Raciocínio','chairs','Seven rooms each have four chairs. Two chairs were removed in total. Final answer only the number of chairs left.', '26', 48)
        text('Controles','hybrid-copy','Escreva exatamente o identificador compressible, sem formatação.', 'compressible', exact=True)
        text('Controles','portuguese','Qual é o plural de pão? Uma palavra.', 'pães')
        text('Controles','translate','Translate green into Portuguese. One word.', 'verde')
        text('Controles','fact','What planet do we live on? One word.', 'Earth')
        text('Controles','identity','Diga apenas sim ou não. Uma baleia é um mamífero?', 'sim')
    return rows, keys


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('folder', type=Path)
    args = p.parse_args()
    args.folder.mkdir(parents=True, exist_ok=True)
    rows = calibration()
    write(args.folder / 'calibration.json', rows)
    seen = {r['prompt'] for r in rows}
    for phase in ('screen', 'final'):
        prompts, keys = suite(phase)
        assert not seen.intersection(row['prompt'] for row in prompts)
        seen.update(row['prompt'] for row in prompts)
        write(args.folder / f'{phase}.prompts.json', prompts)
        write(args.folder / f'{phase}.grading.json', keys)
    files = sorted(args.folder.glob('*.json'))
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    write(args.folder / 'frozen.json', manifest)
