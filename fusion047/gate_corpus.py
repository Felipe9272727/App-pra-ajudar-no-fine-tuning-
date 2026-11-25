"""Extra first-token activations for the identity classifier."""
import argparse
import json
from pathlib import Path

TRAIN = [
    (True, 'Você pode dizer quem é, por favor?'),
    (True, 'Me conta qual modelo está falando comigo.'),
    (True, 'O que eu deveria colocar como seu nome?'),
    (True, 'Dá seu nome e conta de onde você veio.'),
    (True, 'What do you call yourself?'),
    (True, 'Are you the Qwen model? Who is talking to me?'),
    (False, 'Quem fez o ChatGPT?'),
    (False, 'Who owns Google DeepMind?'),
    (False, 'Me descreva o que é um modelo de linguagem.'),
    (False, 'Escreva um programa Python que imprima Liquid Sense na tela.'),
    (False, 'Conte-me a história do Android.'),
    (False, 'Qual o plural de pão?'),
    (False, 'O que é a empresa Google?'),
    (False, 'Quem criou o modelo Gemma 2?'),
    (False, 'Como você resolveria uma equação do segundo grau?'),
    (False, 'Qual é o certo: essa AI é sua ou é de outra pessoa? Explique a gramática da frase.'),
    (False, 'What model did OpenAI release under the GPT-4 name?'),
    (False, 'Tell me how to cook rice.'),
    (False, 'Como você faria para ordenar uma lista em Python?'),
    (False, 'Invente um diálogo entre duas pessoas que acabaram de se conhecer.'),
    (False, 'Defina treinamento supervisionado em duas frases.'),
    (False, 'Qual é o valor de 12 vezes 13?'),
]
DEVELOPMENT = [
    (True, 'Antes de continuar, qual é a identificação do modelo nesta conversa?'),
    (True, 'Você é aquele chatbot do Google ou é outro?'),
    (True, 'Please introduce the AI I am speaking with.'),
    (False, 'O Gemini e a Gemma são de qual empresa?'),
    (False, 'What is the meaning of independent developer?'),
    (False, 'Traduza a expressão Liquid Sense para português.'),
    (False, 'Como fazer concatenação de strings em Python?'),
    (False, 'Qual é a capital da Argentina?'),
    (False, 'Escreva uma apresentação para um pesquisador fictício.'),
]


def build():
    result = []
    for split, prompts in [('train', TRAIN), ('dev', DEVELOPMENT)]:
        for i, (positive, prompt) in enumerate(prompts):
            result.append(dict(id=f'gate/{split}/{i:02}', split=split,
                               domain='gate_yes' if positive else 'gate_no',
                               prompt=prompt, completion='', thought=None))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n')
