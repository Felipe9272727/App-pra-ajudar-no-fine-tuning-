"""Freeze selected weights and all evaluator/data hashes before public outputs."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]


def main():
    assert not (HERE/'frozen.json').exists(),'Already frozen; do not reopen selection'
    assert not list(HERE.glob('results_*.json'))
    selection_path=ROOT/'reasoning/selection.json';selection=json.loads(selection_path.read_text())
    names=['PROTOCOL.md','build_data.py','stdio_judge.py','evaluate.py','prompts.json','oracles.json','selected_ids.json','sources.json']
    paths=[HERE/n for n in names]+list((HERE/'vendor/instruction_following_eval').glob('*.py'))
    paths += [ROOT/n for n in ['reasoning/runtime_helpers.py','code_rsi/runtime.py','v2_adaptation/native_runtime.py','modeling_sensenova_loop.py']]
    frozen={'status':'frozen_before_public_inference','selection_sha256':hashlib.sha256(selection_path.read_bytes()).hexdigest(),
        'selected':selection,'variants':['original','parent','liquid'] if selection.get('patch') else ['original','liquid'],
        'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        'public_outputs_used_for_weight_selection':False}
    (HERE/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n')
    print('PUBLIC_COMPARISON_FROZEN',frozen['variants'])


if __name__=='__main__':main()
