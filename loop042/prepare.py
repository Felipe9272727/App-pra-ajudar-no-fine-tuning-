"""Prepare a reproducible paired sample. Store answers separately from model inputs."""
import argparse
import csv
import hashlib
import json
import random
import zipfile
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[1]


def normalized_options(question, options, answer, name):
    letters = 'ABCDEFGHIJ'[:len(options)]
    rows = '\n'.join(f'{letter}) {choice}' for letter, choice in zip(letters, options))
    prompt = f'{question}\n\n{rows}\n\nEnd with a separate line: Answer: {name} (replace {name} with one letter from {letters}).'
    return prompt, letters[answer]


def prepare(assets, output):
    cases, grading = [], {}

    def add(group, case_id, prompt, grade, response, reasoning=0):
        key = f'{group}/{case_id}'
        assert key not in grading
        cases.append({'id': key, 'group': group, 'prompt': prompt, 'options': {
            'thinking': bool(reasoning), 'reasoning_tokens': reasoning,
            'response_tokens': response, 'context_tokens': 16384}})
        grading[key] = grade

    def rows(source):
        return [row['row'] for row in json.loads((assets / source).read_text())['rows']]

    for index in [0, 4, 9, 15, 20, 25]:
        row = rows('aime.source')[index]
        add('AIME25', row['id'], row['problem'] + '\n\nEnd with a separate line: Answer: N, where N is your final integer.',
            {'type': 'integer', 'expected': int(row['answer'])}, 24, 48)

    with (assets / 'gpqa.source').open(encoding='utf-8-sig') as f:
        gpqa = list(csv.DictReader(f))
    assert len(gpqa) == 198
    for index in [2, 38, 70, 104, 141, 178]:
        row = gpqa[index]
        correct = row['Correct Answer']
        choices = [correct] + [row[f'Incorrect Answer {i}'] for i in range(1, 4)]
        random.Random(42026 + index).shuffle(choices)
        text, expected = normalized_options(row['Question'], choices, choices.index(correct), 'X')
        add('GPQA-Diamond', row['Record ID'], text, {'type':'letter','expected':expected}, 24, 32)

    for index in [102, 1314, 2402, 4488, 6240, 9250]:
        row, = rows(f'mmlu-{index}.source')
        text, expected = normalized_options(row['question'], row['options'], row['answer_index'], 'X')
        assert expected == row['answer']
        add('MMLU-Pro', row['question_id'], text, {'type':'letter','expected':expected}, 24, 24)

    if_cases = [json.loads(line) for line in (assets / 'if.source').read_text().splitlines()]
    assert len(if_cases) == 300
    for index in [0, 48, 96, 144, 192, 240]:
        row = if_cases[index]
        add('IFBench', row['key'], row['prompt'], {'type':'ifbench','row':row}, 96)

    tok = Tokenizer.from_file(str(assets / 'tokenizer.json'))
    with (assets / 'aa.source').open(encoding='utf-8-sig') as f, zipfile.ZipFile(assets / 'aa-text.zip') as files:
        aa = sorted(csv.DictReader(f), key=lambda r: (int(r['input_tokens']), int(r['question_id'])))
        chosen = set()
        for row in aa:
            group = row['document_set_id']
            if group in chosen:
                continue
            chosen.add(group)
            docs = row['data_source_filenames'].split(';')
            excerpts = []
            for name in docs:
                path, = [p for p in files.namelist() if p.endswith(f'/{group}/{name}')]
                source = files.read(path).decode('utf-8-sig')
                ids = tok.encode(source, add_special_tokens=False).ids
                # Fixed leading excerpt from every document. No answer-dependent retrieval.
                excerpts.append(f'Document {name}:\n' + tok.decode(ids[:1024//len(docs)]))
            prompt = '\n\n'.join(excerpts) + '\n\nQuestion: ' + row['question'] + '\nGive a concise answer.'
            add('AA-LCR-recortado', row['question_id'], prompt, {'type':'text','expected':[row['answer']]}, 64)
            if len(chosen) == 2:
                break

    project = ROOT / 'loop042' / 'data'
    for row in json.loads((project / 'validation_code.json').read_text()):
        add('Código029', row['id'], row['prompt'], {'type':'code','cases':row['cases']}, 128)
    for row in json.loads((project / 'legacy_general.json').read_text()):
        add('Controles029', row['id'], row['prompt'], {'type':'legacy_text','expected':row['answers']}, 64)
    # Explicitly known retrieval control, with relevant facts older than the moving window.
    filler = 'The verification log has no other relevant entries. ' * 42
    add('Janela-controle', 'early-code', 'The project verification code is lantern-745.\n' + filler
        + '\nReturn only the project verification code.', {'type':'text','expected':['lantern-745']}, 32)

    def dump(target, value):
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

    output.mkdir(parents=True, exist_ok=True)
    dump(output / 'prompts.json', cases)
    dump(output / 'grading.json', grading)
    source_names = ['aime.source','gpqa.source','if.source','aa.source','aa-text.zip','if-ref.txt']
    source_names += [f'mmlu-{i}.source' for i in [102, 1314, 2402, 4488, 6240, 9250]]
    sources = sorted(assets/name for name in source_names)
    dump(ROOT/'loop042'/'data'/'evaluation_manifest.json', {
        'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'ifbench_revision': (assets/'if-ref.txt').read_text().strip(),
        'cases': [{'id':r['id'],'group':r['group'],'options':r['options'],
                   'prompt_sha256': hashlib.sha256(r['prompt'].encode()).hexdigest()} for r in cases],
    })


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('assets', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    prepare(a.assets, a.output)
