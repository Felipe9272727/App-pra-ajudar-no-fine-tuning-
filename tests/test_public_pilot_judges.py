"""Known scoring edge cases and isolated program I/O, before public inference."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('public_pilot_eval',ROOT/'benchmarks/reasoning_20261105/evaluate.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class PublicPilotJudgeTests(unittest.TestCase):
    def test_exact_numeric_answers_and_ambiguous_lines(self):
        self.assertTrue(module.grade_number('Answer: $1,250.','1250'))
        self.assertTrue(module.grade_number('1/2','0.5'))
        self.assertTrue(module.grade_number('.5','0.5'))
        self.assertFalse(module.grade_number('.5','5'))
        self.assertFalse(module.grade_number('2 or 3','3'))
        self.assertFalse(module.grade_number('0.3333','1/3'))

    def test_real_isolated_stdin_and_import_policy(self):
        oracle={'cases':[{'input':'2 3\n','output':'5\n'},{'input':'-1 4\n','output':'3\n'}]}
        code='import sys\na,b=map(int,sys.stdin.buffer.read().split())\nprint(a+b)'
        self.assertTrue(module.stdio_judge.evaluate(code,oracle)['all_passed'])
        blocked=module.stdio_judge.evaluate('import os\nprint(os.listdir())',oracle)
        self.assertFalse(blocked['all_passed'])
        self.assertEqual(blocked['category'],'ValueError')


if __name__=='__main__':unittest.main()
