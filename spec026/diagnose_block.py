"""Post-timing engineering witness; never rescored or used to change training."""
import json
import os
from pathlib import Path
import torch
from target_model import load_target
from io_parts import load_draft, save_json
from spec_engine import Engine, serial, speculative, install_cached_recurrent_rule

H = Path(__file__).resolve().parent


class ObservedTarget(Engine):
    def __init__(self, model):
        super().__init__(model, 'target_diagnostic')
        self.references = {}
        self.collect = True
        self.comparisons = []

    def forward(self, ids, cache=None, all_logits=False):
        tokens = ids[0].tolist() if torch.is_tensor(ids) else list(ids)
        before = list(getattr(cache, '_spec026_debug_tokens', [])) if cache is not None else []
        logits, result = super().forward(ids, cache, all_logits)
        result._spec026_debug_tokens = before + tokens
        positions = list(range(len(tokens))) if all_logits else [len(tokens) - 1]
        for index, position in enumerate(positions):
            key = tuple(before + tokens[:position + 1])
            vector = logits[index]
            if self.collect:
                self.references[key] = vector.clone()
            elif key in self.references:
                ref = self.references[key]
                top = ref.topk(2).values
                self.comparisons.append({
                    'processed_prefix_tokens': len(key), 'forward_input_tokens': len(tokens),
                    'position_within_forward': position,
                    'max_abs_logit_difference_same_token_prefix': float((vector - ref).abs().max()),
                    'reference_argmax': int(ref.argmax()), 'observed_argmax': int(vector.argmax()),
                    'reference_top_two_logit_margin': float(top[0] - top[1]),
                })
        return logits, result


@torch.inference_mode()
def main():
    out = H / 'reports/block_diagnostic.json'
    assert not out.exists(), 'Do not repeat a completed engineering witness'
    assert json.loads((H / 'reports/speed_summary.json').read_text())['status'] == 'complete'
    install_cached_recurrent_rule()
    torch.set_num_threads(4)
    model, tok, meta = load_target()
    small, _ = load_draft('small')
    large, _ = load_draft('large')
    question = next(x for x in json.loads((H / 'data/speed_prompts.json').read_text()) if x['id'] == 'S026S/5')
    prefix = tok.apply_chat_template([{'role': 'user', 'content': question['prompt']}],
        tokenize=True, return_dict=False, add_generation_prompt=True, enable_thinking=False)
    target = ObservedTarget(model)
    reference = serial(target, prefix, 16)
    saved = [x for x in json.loads((H / 'reports/parity.json').read_text())['rows'] if x['id'] == question['id']]
    assert all(reference['ids'] == x['reference_ids'] for x in saved)
    target.collect = False
    block = speculative(target, Engine(small, 'small'), prefix, 16, 4, verify_mode='block')
    block_comparisons = target.comparisons
    mismatches = [x for x in block_comparisons if x['reference_argmax'] != x['observed_argmax']]
    fallbacks = {}
    for size, child in [('small', small), ('large', large)]:
        target.comparisons = []
        result = speculative(target, Engine(child, size), prefix, 16, 4, verify_mode='serial')
        fallbacks[size] = {'ids': result['ids'], 'identical_to_serial_target': result['ids'] == reference['ids'],
            'max_abs_logit_difference_same_prefix': max((x['max_abs_logit_difference_same_token_prefix'] for x in target.comparisons), default=0.)}
        print('FALLBACK_WITNESS', size, fallbacks[size]['identical_to_serial_target'], flush=True)
    report = {'status': 'complete', 'scope': 'post-timing diagnostic, not an additional performance trial',
        'id': question['id'], 'reference_ids': reference['ids'], 'block_small_ids': block['ids'],
        'original_small_mismatch_reproduced': block['ids'] == next(x['speculative_ids'] for x in saved if x['size'] == 'small'),
        'block_matches_target': block['ids'] == reference['ids'],
        'block_logit_comparisons_at_identical_token_prefixes': block_comparisons,
        'argmax_disagreements_at_identical_token_prefixes': mismatches,
        'serial_fallbacks': fallbacks, 'weights_judges_and_primary_results_changed': False,
        'causal_limit': 'This isolates execution-path differences at equal token prefixes. It does not identify the unique first diverging operation or prove a rounding-only cause; block mode remains ineligible.'}
    save_json(out, report)
    print('BLOCK_DIAGNOSTIC_COMPLETE', report['original_small_mismatch_reproduced'], len(mismatches), flush=True)


if __name__ == '__main__':
    s = json.loads((H / 'status.json').read_text())
    s.update(status='running_post_timing_block_diagnostic', model_process_active=True)
    save_json(H / 'status.json', s)
    save_json(H / 'runtime.json', {'phase': 'block_diagnostic', 'pid': os.getpid(), 'single_worker': True})
    succeeded = False
    try:
        main()
        succeeded = True
    finally:
        s = json.loads((H / 'status.json').read_text())
        s.update(status='completed_post_timing_block_diagnostic' if succeeded else 'failed_post_timing_block_diagnostic', model_process_active=False)
        save_json(H / 'status.json', s)
        save_json(H / 'runtime.json', {'phase': 'block_diagnostic', 'pid': None, 'model_process_active': False})
