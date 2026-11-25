"""Colab entry point with source checks for ambiguous and verifiable requests."""
import hashlib
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from types import MethodType, ModuleType
import unicodedata
from urllib.request import urlopen

REPO = 'https://raw.githubusercontent.com/Felipe9272727/App-pra-ajudar-no-fine-tuning-'
BASE = '50ef8eef309bc1a58a332a102c8d93d7b7905971'
NOTEBOOK_SHA = '7be42710a18a3ae6436c8a64faa888ba54d441f0a8c83f7eac75a3ab4bd11bec'
RUNTIME_SHA = 'cef33cc8a840c07e95f2c294c15a8184c82f1a4eca23277972cbb3c226fd688e'
THINKING_SHA = '963edbdea13568a054ef7b73e00453e2df033446a02e6b9af97c891072300fa8'
ADAPTER_SHA = '941daca310736af121cdd337317b5e1bddb741b88ea085d684d3760ecc1fecfd'

COMMON_TOOLS = set('git python python3 pip pip3 npm npx node cargo rustc docker kubectl uv curl'.split())
COMMAND = re.compile(r'(?<![\w./-])([a-z][\w.-]{0,39}) +'
                     r'(serve|deploy|build|config|install|start|init|login|sync|run|status|version|--[\w-]+)(?![\w-])')
QUOTED_COMMAND = re.compile(r'`([a-z][\w.-]{0,39}) +([a-z][\w.-]{0,39}|--[\w-]+)(?: +[^`\n]*)?`')
TECHNICAL = re.compile(r'\b(comando|terminal|cli|usar|uso|executar|rodar|codifica\w*|programa\w*|'
                       r'flag|servidor|command|usage|use|coding|deploy)\b')
CLI_CONTEXT = re.compile(r'\b(comando|terminal|cli|subcomando|command|shell)\b')
CODING_CAPABILITY = re.compile(
    r'^\s*(?:(?:oi|ei|eai|fala|mano)[,! ]+)*\b(?:vc|voce|tu)\s+'
    r'(?:serve\s+(?:pra|para)|(?:pode|consegue|sabe|ajuda\s+a))\s+'
    r'(?:ajudar\s+(?:a|com)\s+)?(?:codifica\w*|programa\w*|(?:escrever|revisar)\s+codigos?)\b'
    r'(?:[, ]+(?:certo|ne|nao e|mesmo))?[ ?.!]*$',
)
REQUESTS_SOURCE = re.compile(r'\b(pesquise|busque|consulte|verifique|procure)\b.{0,55}'
                             r'\b(web|internet|documentacao|fonte|site|manual)\b|'
                             r'\b(search|browse|look up)\b.{0,55}\b(web|online|docs|documentation)\b|'
                             r'\b(cite|cite-me|mostre|provide)\s+(?:a |uma |as |an? |the )?'
                             r'(fontes?|citac\w+|referencia|source|citation)\b|'
                             r'\b(versao (mais recente|atual)|latest version|preco atual|'
                             r'cotacao atual|quanto custa hoje|dados em tempo real|lancou (ontem|hoje))\b')
CLAIMS_ACTION = re.compile(r'(?:^|[.!?\n]\s*)[\s*]*(?:eu )?'
                           r'(?:pesquisei|busquei|consultei|verifiquei na internet|'
                           r'(?:executei|rodei|testei) (?:o |este |esse )?(?:codigo|script|comando)|'
                           r'i (?:searched|browsed|ran the (?:code|script|command)|tested the code))\b')
ASKS_IDENTITY = re.compile(r'\b(quem (?:e voce|te (?:criou|desenvolveu))|'
                           r'seu nome|como (?:devo|posso) (?:te )?chamar|'
                           r'voce e (?:o |um |da |do )?(?:qwen|google|gemini|alibaba)|'
                           r'who (?:are you|built you)|what is your (?:model )?name)\b')
FALSE_IDENTITY = re.compile(r"\b(?:sou|i am|i'm)\s+(?:(?:o|a|um|an|the)\s+)?(?:qwen[\d.]*|gemini)\b")
WORDS = re.compile(r'[\w.-]+')
STOP_WORDS = set('como para sobre qual quais seria pode mostre diga explique fonte manual '
                 'documentacao posso essa esse isso esta este usar funciona usando serve existe atual '
                 'cite procure pesquise busque consulte verifique com por que uma um'.split())


def normalize(text):
    folded = unicodedata.normalize('NFKD', text.casefold())
    return ''.join(c for c in folded if not unicodedata.combining(c))


def unknown_command(question):
    for match in QUOTED_COMMAND.finditer(question):
        command = f'{match[1]} {match[2]}'
        if match[1] not in COMMON_TOOLS and (CLI_CONTEXT.search(question) or COMMAND.fullmatch(command)):
            return command
    for match in COMMAND.finditer(question):
        if match[1] in COMMON_TOOLS or match[1] in {'o', 'a', 'eu', 'ele', 'ela', 'voce', 'que', 'isso'}:
            continue
        if match[1] == 'vc' and re.search(r'\b(pra|para) que $', question[:match.start()]) and not CLI_CONTEXT.search(question):
            continue
        if TECHNICAL.search(question) or question.rstrip(' ?!.') == match[0]:
            return match[0]
    return None


def source_answer(question, reference):
    """For evidence-dependent turns, use literal excerpts or ask a clarification."""
    normalized = normalize(question)
    if not reference and CODING_CAPABILITY.fullmatch(normalized.strip(" \"'“”")):
        return dict(text=('Sim. Posso ajudar a escrever, explicar e revisar código, '
                          'além de sugerir testes. Me diga o que você quer programar '
                          'ou cole o trecho e a mensagem de erro.'), mode='capabilities')
    command = unknown_command(normalized)
    if not (command or reference or REQUESTS_SOURCE.search(normalized)):
        return None
    terms = {word for word in WORDS.findall(normalized) if len(word) >= 3 and word not in STOP_WORDS}
    if reference:
        if command:
            pattern = re.compile(r'(?<![\w.-])' + r'\s+'.join(map(re.escape, command.split())) + r'(?![\w.-])')
            match = pattern.search(normalize(reference))
            if match:
                # Find the matching original line so accents and documented syntax survive.
                lines = reference.splitlines()
                for i, line in enumerate(lines):
                    if pattern.search(normalize(line)):
                        quote = '\n'.join(lines[max(0, i-1):i+4]).strip()[:900]
                        return dict(text=f'Na referência fornecida para `{command}`:\n\n{quote}', mode='source')
        elif terms:
            paragraphs = re.split(r'\n\s*\n', reference.strip())
            matches = [(len(terms & set(WORDS.findall(normalize(p)))), p) for p in paragraphs]
            score, quote = max(matches, key=lambda pair: pair[0])
            if score >= min(2, len(terms)):
                return dict(text=f'Trecho da referência fornecida:\n\n{quote[:900]}', mode='source')
    if command:
        return dict(text=(f'Qual ferramenta fornece `{command}` e qual é a versão? '
                          'Cole a saída de ajuda ou o trecho da documentação para eu conseguir conferir.'),
                    mode='clarify')
    return dict(text='Qual fonte posso usar para conferir? Cole aqui o trecho relevante da documentação ou dos dados.',
                mode='clarify')


def verify_result(question, result):
    answer = normalize(result['text'])
    if CLAIMS_ACTION.search(answer):
        return {**result, 'mode': 'unverified',
                'text': 'Essa resposta precisaria de uma busca ou execução verificável. '
                        'Cole a fonte ou a saída que você obteve para eu analisar.'}
    if ASKS_IDENTITY.search(normalize(question)) and (
            FALSE_IDENTITY.search(answer) or
            (result.get('identity_active') and 'liquid sense' not in answer)):
        return {**result, 'mode': 'checkpoint_metadata',
                'text': 'Checkpoint carregado: Liquid Sense 047, projeto de um desenvolvedor independente.'}
    return {**result, 'mode': 'model'}


def download(url, expected_sha, limit):
    with urlopen(url, timeout=45) as response:
        content = response.read(limit + 1)
    if len(content) > limit or hashlib.sha256(content).hexdigest() != expected_sha:
        raise RuntimeError(f'SHA-256 inválido para {url.rsplit("/", 1)[-1]}.')
    return content


class ColabChat:
    def __init__(self, revision, model=None):
        self.root = f'{REPO}/{revision}/fusion047'
        self.model = model

    def load(self):
        if getattr(self.model, 'identity', None) is None:
            import torch

            base = f'{REPO}/{BASE}/fusion047/LiquidSense047.ipynb'
            notebook = json.loads(download(base, NOTEBOOK_SHA, 16000))
            setup = ''.join(notebook['cells'][1]['source'])
            if not torch.cuda.is_available():
                setup = setup.replace('usar_t4 = True', 'usar_t4 = False', 1)
            namespace = {}
            exec(compile(setup, 'liquid_sense_047_setup.py', 'exec'), namespace)
            self.model = namespace['model']
        if getattr(self.model, '_thinking_head_sha', None) != THINKING_SHA:
            runtime = ModuleType('liquid_sense_047_thinking')
            source = download(f'{self.root}/torch_runtime.py', RUNTIME_SHA, 40000)
            exec(compile(source, 'liquid_sense_047_thinking.py', 'exec'), runtime.__dict__)
            with NamedTemporaryFile(suffix='.npz') as weights:
                weights.write(download(f'{self.root}/checkpoints/identity-thinking.npz', THINKING_SHA, 250000))
                weights.flush()
                identity = runtime.LiquidSenseTorch.load_identity(
                    self.model, Path(weights.name), THINKING_SHA, ADAPTER_SHA)
            self.model.thinking_identity = identity[:2]
            self.model.generate = MethodType(runtime.LiquidSenseTorch.generate, self.model)
            self.model._thinking_head_sha = THINKING_SHA
        return self.model

    def ask(self, question, *, thinking=True, reasoning_tokens=192, response_tokens=256, reference=''):
        if not isinstance(question, str) or not question.strip():
            raise ValueError('Escreva uma pergunta.')
        evidence = source_answer(question, reference.strip())
        if evidence is not None:
            return evidence
        result = self.load().generate(question, thinking=thinking, reasoning_tokens=reasoning_tokens,
                                      response_tokens=response_tokens, stop_repetition=True)
        return verify_result(question, result)
