import importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rsi100_policy',ROOT/'rsi100/policy.py');policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
class RSI100Tests(unittest.TestCase):
 def score(self,bits,controls=None,nll=2.):
  return {'rows':[{'id':'a','case_passed':bits}],'control_bits':[True,True] if controls is None else controls,'anchor_nll':nll}
 def test_accepts_strict_gain_without_losing_correct_cases(self):
  self.assertTrue(policy.accept(self.score([True,True,False]),self.score([True,False,False]))[0])
 def test_discards_ties_and_accuracy_tradeoffs(self):
  old=self.score([True,False,False])
  self.assertFalse(policy.accept(self.score([True,False,False]),old)[0])
  self.assertFalse(policy.accept(self.score([False,True,True]),old)[0])
 def test_discards_control_and_language_regressions(self):
  old=self.score([True,False])
  self.assertFalse(policy.accept(self.score([True,True],controls=[False,True]),old)[0])
  self.assertFalse(policy.accept(self.score([True,True],nll=2.01),old)[0])
  self.assertFalse(policy.accept(self.score([True,True],nll=float('nan')),old)[0])
 def test_rejects_different_case_sets(self):
  with self.assertRaises(ValueError):policy.accept(self.score([True,True]),self.score([False]))
 def test_budget_and_fresh_task_splits(self):
  data=json.loads((ROOT/'rsi100/data.json').read_text());old=json.loads((ROOT/'code_rsi/data.json').read_text())
  self.assertEqual(data['protocol']['rounds'],100)
  prior={r['prompt'] for k in ['train','development','validation','heldout'] for r in old[k]}
  seen=set(prior)
  for key,count in [('validation',8),('heldout',16)]:
   self.assertEqual(len(data[key]),count)
   for row in data[key]:
    self.assertNotIn(row['prompt'],seen);seen.add(row['prompt'])
if __name__=='__main__':unittest.main()
