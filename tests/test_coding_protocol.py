import ast
import json
import math
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'code_rsi'))
# Load explicitly because older pilots also have a publish module.
from sandbox import extract_code,check_ast,execute_payload,same_value
from loop_protocol import visit_gains,eligibility,validation_passes

class CodingProtocolTests(unittest.TestCase):
    def test_loop_plans_share_total_gain_and_keep_all_visits_active(self):
        for passes in [2,3,4]:
            gains=visit_gains(passes)
            self.assertEqual(len(gains),passes);self.assertAlmostEqual(sum(gains),1.)
            self.assertTrue(all(g>0 for g in gains));self.assertEqual(8+24*passes,{2:56,3:80,4:104}[passes])
        for passes in [0,1,5]:
            with self.assertRaises(ValueError):visit_gains(passes)

    def test_actual_shared_execution_plan_without_importing_ml_runtime(self):
        # Exercise the actual pure function from the model, no fake reimplementation.
        tree=ast.parse((ROOT/'modeling_sensenova_loop.py').read_text())
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='execution_plan')
        code=ast.Module(body=[fn],type_ignores=[]);ns={"math":math};exec(compile(code,'plan','exec'),ns)
        cfg=json.loads((ROOT/'sensenova_config.json').read_text())
        for passes in [2,3,4]:
            cfg['loop_settings']['eval_count']=passes;cfg['loop_settings']['counts']=[passes]
            plan=ns['execution_plan'](cfg)
            self.assertEqual(len(plan),8+24*passes)
            self.assertEqual(list(plan).count(4),passes)

    def test_reference_data_does_not_enter_prompts(self):
        data=json.loads((ROOT/'code_rsi/data.json').read_text());seen=set()
        for split,count in [('train',8),('development',8),('validation',8),('heldout',24)]:
            self.assertEqual(len(data[split]),count)
            for row in data[split]:
                self.assertNotIn(row['id'],seen);seen.add(row['id'])
                self.assertNotIn('expected',row['prompt']);self.assertNotIn('assert ',row['prompt'])
                self.assertGreaterEqual(len(row['cases']),4)
        self.assertFalse(data['protocol']['test_answer_in_prompt'])

    def test_code_extraction_does_not_invent_a_solution(self):
        self.assertEqual(extract_code('```python\ndef solve(x):\n    return x+1\n```'),'def solve(x):\n    return x+1')
        self.assertEqual(extract_code('<think>still working'), '')
        self.assertEqual(extract_code('<think>private</think>def solve(x):\n    return x'),'def solve(x):\n    return x')

    def test_no_io_reflection_or_imports_in_generated_function_subset(self):
        for code in ['import os\ndef solve(x): return x','def solve(x): return open("x").read()', 'def solve(x): return x.__class__', 'def solve(x): return globals()', 'def solve(x):\n    print(x)\n    return 1']:
            with self.subTest(code=code):
                with self.assertRaises(ValueError):check_ast(code)
        check_ast('def solve(xs):\n    return sorted(xs, key=lambda x: -x)')
        check_ast('def solve(xs):\n    return list(dict.fromkeys(xs))')

    def test_valid_wrong_runtime_and_syntax_are_distinct(self):
        cases=[{'args':[[1,2]],'expected':3},{'args':[[]],'expected':0}]
        correct=execute_payload({'code':'def solve(xs): return sum(xs)','cases':cases})
        self.assertTrue(correct['all_passed'])
        wrong=execute_payload({'code':'def solve(xs): return len(xs)','cases':cases})
        self.assertEqual(wrong['category'],'WrongReturnValue');self.assertEqual(wrong['passed'],1)
        runtime=execute_payload({'code':'def solve(xs): return xs[0]','cases':cases})
        self.assertIn('IndexError',runtime['error_types'])
        syntax=execute_payload({'code':'def solve(:','cases':cases})
        self.assertEqual(syntax['category'],'SyntaxError')
        self.assertFalse(same_value(1,True));self.assertTrue(same_value(1,1.0))

    def test_promotion_gates_do_not_reward_syntax_only_improvement(self):
        base={'tasks_passed':3,'controls_correct':4,'anchor_nll':2.0}
        candidate={**base,'tasks_passed':4,'anchor_nll':2.03}
        self.assertTrue(eligibility(candidate,base));self.assertTrue(validation_passes(candidate,base))
        self.assertFalse(eligibility({**candidate,'controls_correct':3},base))
        self.assertFalse(eligibility({**candidate,'anchor_nll':2.1},base))
        self.assertFalse(validation_passes(base,base))

if __name__=='__main__':unittest.main()
