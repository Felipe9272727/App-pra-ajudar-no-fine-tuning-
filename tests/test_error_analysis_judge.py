import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('separate_judge_v2',ROOT/'reasoning/cycle2/stdio_judge_v2.py')
judge=importlib.util.module_from_spec(spec);spec.loader.exec_module(judge)

class ErrorAuditJudgeTests(unittest.TestCase):
    def test_private_local_and_iterator_are_valid_python(self):
        code='import sys\n_it=iter(map(int,sys.stdin.read().split()))\nn=next(_it)\n_total=0\nfor _ in range(n):\n _total+=next(_it)\nprint(_total)'
        result=judge.evaluate(code,{'cases':[{'input':'3 2 3 4\n','output':'9\n'},
            {'input':'0\n','output':'0\n'}]})
        self.assertTrue(result['all_passed'])

    def test_unsafe_access_remains_rejected(self):
        for code in ['import os\nprint(os.environ)', 'print(open("/etc/hostname").read())',
                     'print(__builtins__)', 'print((1).__class__)', 'exec("print(1)")']:
            with self.subTest(code=code):
                with self.assertRaises((ValueError,SyntaxError)):judge.validate(code)

if __name__=='__main__':unittest.main()
