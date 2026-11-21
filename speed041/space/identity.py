"""Product identity for direct questions in the Space chat."""

import re
import unicodedata


DESCRIPTION = (
    'Sou o Liquid Sense, um modelo experimental criado por um único desenvolvedor independente. '
    'Minha base é o Qwen3.5-0.8B, com adaptações inspiradas em SenseNova Loop e Liquid AI '
    'para aprimorar programação e raciocínio.'
)
PORTUGUESE = {
    'quem e voce', 'quem voce e', 'quem e vc', 'quem vc e', 'qual e o seu nome',
    'qual o seu nome', 'como voce se chama', 'como vc se chama', 'que modelo voce e',
    'qual modelo voce e', 'voce e qwen', 'voce e o qwen', 'voce e o liquid sense',
    'vc e qwen', 'se apresente', 'apresente se', 'quem e voce e como foi criado',
    'quem e voce e porque e como foi criado', 'quem e voce e por que e como foi criado',
}
ENGLISH = {'who are you', 'what is your name', 'what s your name', 'what model are you',
           'are you qwen', 'are you liquid sense', 'introduce yourself'}


def direct_identity(question):
    if not isinstance(question, str) or len(question) > 140:
        return None
    normalized = ''.join(c for c in unicodedata.normalize('NFD', question.lower())
                         if not unicodedata.combining(c))
    normalized = re.sub('[^a-z0-9]+', ' ', normalized).strip()
    normalized = re.sub(r'^(?:(?:oi|ola|eai|e ai|mano|mn) )+', '', normalized)
    if normalized in PORTUGUESE:
        return DESCRIPTION
    if normalized == 'quem e voce e voce e melhor que os melhores modelos':
        return DESCRIPTION + ' Para comparar meu desempenho com outros modelos, é preciso olhar os resultados em cada tarefa.'
    if normalized in ENGLISH:
        return ('I’m Liquid Sense, an experimental model built by one independent developer. '
                'I’m based on Qwen3.5-0.8B, with adaptations inspired by SenseNova Loop and Liquid AI '
                'to improve coding and reasoning.')
    return None
