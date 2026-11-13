"""Post-evaluation descriptive error audit; no weight, judge or label changes."""
import ast
import collections
from pathlib import Path
from io_parts import save_json
import json
from code_rsi.sandbox import extract_code

H = Path(__file__).resolve().parent


def main():
    variants = {}
    for size in ['small', 'large']:
        r = json.loads((H / 'reports' / f'quality_{size}_trained.json').read_text())
        assert r['status'] == 'complete'
        outputs = collections.Counter(x['text'] for x in r['code'])
        parsed = []
        for row in r['code']:
            try:
                tree = ast.parse(extract_code(row['text']))
                valid = any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in tree.body)
            except (SyntaxError, ValueError):
                valid = False
            parsed.append({'id': row['id'], 'parseable_function': valid,
                           'passed_cases': row['passed'], 'all_cases': row['total']})
        variants[size] = {
            'distinct_code_outputs_for_8_requests': len(outputs),
            'most_frequent_output': outputs.most_common(1)[0][0],
            'most_frequent_output_count': outputs.most_common(1)[0][1],
            'parseable_function_outputs': sum(x['parseable_function'] for x in parsed),
            'code_rows': parsed,
            'general_outputs_starting_def': sum(x['text'].lstrip().startswith('def ') for x in r['general']),
            'general_correct': r['general_correct'],
        }
    save_json(H / 'reports/failure_analysis.json', {
        'scope': 'descriptive audit of already-completed standalone outputs',
        'variants': variants,
        'training_or_judges_changed': False,
        'interpretation': 'Small child emits incomplete program templates; large child repeats a largely fixed program. Train NLL did not establish instruction following or fresh-task competence.',
        'causal_limits': 'No matched architecture/data/objective ablation was run; do not identify a unique culpable tensor or blame the loop from these observations.',
        'next_hypothesis_not_executed': 'Much broader pretraining/teacher data and an assistant-focused objective may improve conditioning and acceptance; requires a new preregistration and fresh reserved evaluations.',
    })


if __name__ == '__main__':
    main()
