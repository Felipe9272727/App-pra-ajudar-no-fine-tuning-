"""Score identity and regressions without changing the evaluation prompts."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fusion046.corpus import suite
from loop042.score import grade, text_key

WRONG = re.compile(
    r"\b(?:sou|i am|i'm|my name is|me chamo)\s+(?:o\s+|an?\s+)?(?:gemini|google|qwen|chatgpt)"
    r"|(?:desenvolvid[oa]|criad[oa]|developed|created|built)"
    r"\s+(?:pel[oa]s?\s+|por\s+|by\s+)(?:a\s+|o\s+|the\s+)?(?:google|openai|alibaba)"
    r"|\b(?:modelo|ia|assistente)\s+d[oa]\s+google\b"
)
INDEPENDENT = re.compile(r'\bindepend\w+|\b(?:um|one|a)\s+(?:único|single)\s+(?:desenvolvedor|developer)')


def evaluate(fixtures, phase, results):
    prompts = json.loads((fixtures/f'{phase}.json').read_text())
    old_prompts, old_keys = suite('final')
    code_keys = {row['prompt']: old_keys[row['id']] for row in old_prompts if row['group']=='Código'}
    report = {}
    for filename in results:
        raw = [json.loads(line) for line in filename.read_text().splitlines()]
        assert [r['id'] for r in raw] == [r['id'] for r in prompts]
        counts = {'identity': [0,0], 'fact': [0,0], 'control': [0,0], 'code': [0,0]}
        details = []
        for prompt, row in zip(prompts, raw):
            if 'error' in row:
                raise RuntimeError(row['error'])
            answer = row['answer']['text']
            normalized = re.sub(r'[*_`]', '', text_key(answer))
            group = prompt['group']
            extra = {}
            if group in ('name', 'creator'):
                key = 'identity'
                false_claim = bool(WRONG.search(normalized))
                ok = ('liquid sense' in normalized and not false_claim
                      and (group=='name' or bool(INDEPENDENT.search(normalized))))
                extra = {'false_affiliation': false_claim}
            elif group == 'fact':
                key = group
                ok = normalized.rstrip('!?.') in ('google', 'google deepmind', 'deepmind')
            elif group == 'code':
                key = group
                ok, extra = grade(answer, code_keys[prompt['prompt']])
            else:
                key = 'control'
                expected = group.removeprefix('text-')
                ok = normalized.rstrip('!?.') == expected
            if 'identity_active' in row['answer']:
                extra['identity_active'] = row['answer']['identity_active']
            counts[key][0] += int(ok)
            counts[key][1] += 1
            details.append(dict(id=row['id'], group=key, passed=ok, answer=answer, **extra))
        report[filename.stem.removesuffix(f'-{phase}')] = dict(
            counts=counts, code_cases=sum(r.get('passed_cases',0) for r in details),
            false_affiliations=sum(r.get('false_affiliation',False) for r in details),
            examples=details)
    return report


def choose(report):
    parent = report['parent']
    candidates = ['preserve', 'identity']
    # Require a demonstrated improvement and preserve factual and language controls.
    valid = [name for name in candidates if
             report[name]['counts']['identity'][0] > parent['counts']['identity'][0]
             and all(report[name]['counts'][k][0] >= parent['counts'][k][0] for k in ('fact','control'))]
    pool = valid or candidates
    best = max(pool, key=lambda name: (report[name]['counts']['identity'][0],
                                       -report[name]['false_affiliations'], name=='preserve'))
    return dict(variant=best, screen_pass=best in valid)


def gate(report, selected):
    old, new = report['parent'], report[selected['variant']]
    checks = {'development':selected['screen_pass'],
              'identity':new['counts']['identity'][0] >= max(4, old['counts']['identity'][0]+1),
              'facts':new['counts']['fact'][0] >= old['counts']['fact'][0],
              'language':new['counts']['control'][0] >= old['counts']['control'][0],
              'code':new['code_cases'] >= old['code_cases']}
    return dict(eligible=all(checks.values()), checks=checks)


def choose_head(report):
    parent, head = report['parent'], report['head']
    genuine = head['counts']['identity'][0] >= max(2, parent['counts']['identity'][0]+1)
    controls = all(head['counts'][k][0] >= parent['counts'][k][0] for k in ('fact','control'))
    return dict(variant='head', screen_pass=genuine and controls)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('fixtures',type=Path)
    p.add_argument('phase',choices=('screen','final'))
    p.add_argument('results',nargs='+',type=Path)
    a = p.parse_args()
    print(json.dumps(evaluate(a.fixtures,a.phase,a.results),ensure_ascii=False,indent=2))
