import importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('focus_selectivity',ROOT/'code_focus/selectivity.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class FocusTests(unittest.TestCase):
 def test_target_and_active_control_are_distinct_equal_size_and_reproducible(self):
  code=[1.+i%13 for i in range(256)];prose=[x*.1 if i<80 else x*2 for i,x in enumerate(code)]
  selected,control,scores=m.choose_channels(code,prose,16,123)
  self.assertEqual(len(set(selected)),16);self.assertEqual(len(set(control)),16)
  self.assertFalse(set(selected)&set(control));self.assertTrue(all(i<80 for i in selected))
  self.assertEqual((selected,control,scores),m.choose_channels(code,prose,16,123))
 def test_nonfinite_or_empty_activity_cannot_be_called_localization(self):
  for a,b in [([0.]*128,[0.]*128),([float('nan')]*128,[1.]*128)]:
   with self.assertRaises(ValueError):m.choose_channels(a,b,16,1)
 def test_transfer_tasks_are_new_to_both_previous_experiments(self):
  old=json.loads((ROOT/'code_rsi/data.json').read_text());search=json.loads((ROOT/'rsi100/data.json').read_text());data=json.loads((ROOT/'code_focus/data.json').read_text())
  seen={r['prompt'] for key in ['train','development','validation','heldout'] for r in old[key]}
  seen|={r['prompt'] for key in ['search','guard','validation','heldout'] for r in search[key]}
  for key in ['validation','heldout']:
   self.assertEqual(len(data[key]),8)
   for r in data[key]:self.assertNotIn(r['prompt'],seen);seen.add(r['prompt'])
  self.assertFalse(data['protocol']['reference_answers_in_prompts'])
if __name__=='__main__':unittest.main()
