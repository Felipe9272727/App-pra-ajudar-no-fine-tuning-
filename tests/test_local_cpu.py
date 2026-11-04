import importlib.util,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('local_sandbox',ROOT/'local_cpu/sandbox.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)

class LocalCpuTests(unittest.TestCase):
    def test_syscall_access_is_denied_and_capabilities_are_cleared(self):
        self.assertEqual(s.run({'probe':True}),{'denied':{'filesystem':True,'network':True,'process':True},'capabilities_cleared':True})
    def test_correct_and_wrong_functions_use_existing_case_judge(self):
        task={'cases':[{'args':[[2,3]],'expected':5},{'args':[[]],'expected':0}]}
        self.assertEqual(s.evaluate('def solve(xs): return sum(xs)',task)['case_passed'],[True,True])
        self.assertEqual(s.evaluate('def solve(xs): return len(xs)',task)['case_passed'],[False,True])
    def test_imports_and_file_access_are_rejected(self):
        task={'cases':[{'args':[[]],'expected':0}]}
        for code in ['import os\ndef solve(xs): return 0','def solve(xs): return open("/etc/hostname").read()']:
            result=s.evaluate(code,task)
            self.assertEqual(result['passed'],0)
            self.assertEqual(result['category'],'ContractError')
    def test_unbounded_loop_is_stopped_by_cpu_limit(self):
        result=s.evaluate('def solve(xs):\n    while True:\n        pass',{'cases':[{'args':[[]],'expected':0}]})
        self.assertEqual(result['passed'],0)
        self.assertEqual(result['category'],'ResourceLimit')
