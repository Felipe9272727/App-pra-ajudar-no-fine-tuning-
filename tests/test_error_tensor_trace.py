import sys,unittest
from pathlib import Path
from collections import defaultdict,Counter
from types import SimpleNamespace
import torch
from torch import nn
import torch.nn.functional as F
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from diagnostic011.instrument import ParameterAccess,last_decision,stats
from diagnostic011.metric import compare,summarize

def observer(weight):
 return SimpleNamespace(running=True,storage_index={weight.untyped_storage().data_ptr():0},current_reads=[[0],[0],[0]],
  operator_counts=defaultdict(Counter),reader_uses=defaultdict(set),stack=[('owner',0)],reader_priority=[-1],current_reader=[None])

def result(bits):
 return {'model_id':'Qwen/Qwen3.5-4B','model_revision':'fixed-revision','protocol':{'budget':160},
  'rows':[{'id':str(i),'all_passed':b,'passed':int(b)*4,'total':4} for i,b in enumerate(bits)]}

class ErrorTensorTraceTests(unittest.TestCase):
 def test_functional_conv_weight_is_seen_without_calling_module_forward(self):
  conv=nn.Conv1d(2,2,3,groups=2,bias=False);calls=[];handle=conv.register_forward_hook(lambda *a:calls.append(1))
  o=observer(conv.weight)
  with ParameterAccess(o):F.conv1d(torch.ones(1,2,8),conv.weight,groups=2)
  handle.remove();self.assertEqual(calls,[]);self.assertGreater(o.current_reads[2][0],0)
 def test_zero_linear_weight_alias_and_views_still_have_math_access(self):
  w=nn.Parameter(torch.zeros(3,4));alias=w;o=observer(w)
  with ParameterAccess(o):torch.ones(2,4)@alias.T
  self.assertGreater(o.current_reads[0][0],0);self.assertGreater(o.current_reads[2][0],0)
  self.assertEqual(o.current_reader[0],('owner',0));self.assertEqual(len(o.storage_index),1)
 def test_copy_transform_is_not_mislabeled_as_original_storage_matmul(self):
  w=nn.Parameter(torch.ones(3,4,dtype=torch.bfloat16));o=observer(w)
  with ParameterAccess(o):z=w.float()
  self.assertGreater(o.current_reads[1][0],0);self.assertEqual(o.current_reads[2][0],0)
 def test_last_decision_includes_all_gated_value_heads(self):
  m=nn.Module();m._diag_last_token_heads=3;x=torch.arange(5*3*4).reshape(15,4)
  self.assertTrue(torch.equal(last_decision(x,m),x[-3:]))
  y=torch.arange(1*5*3*4).reshape(1,5,3,4);self.assertTrue(torch.equal(last_decision(y),y[0,-1]))
  self.assertEqual(int(last_decision(torch.tensor([[4,8,9]]),nn.Embedding(10,4))),9)
 def test_statistics_identify_zeros_and_nonfinite(self):
  s=stats(torch.tensor([0.,0.,3.,4.,float('inf')]))
  self.assertAlmostEqual(s[0],2.5);self.assertEqual(s[3],.5);self.assertEqual(s[4:], [1,5])
 def test_missing_4b_never_returns_a_fake_gap(self):
  r=compare(result([True,False]));self.assertIsNone(r['delta_pp']);self.assertFalse(r['coding_superiority_confirmed'])
 def test_case_improvement_without_a_complete_task_does_not_change_primary(self):
  a=result([False]);a['rows'][0]['passed']=3
  self.assertEqual(summarize(a['rows'])['problem_pass_at_1'],0)
 def test_mismatched_inference_or_problem_pairs_rejected(self):
  a=result([True]);b=result([False]);b['protocol']['budget']=1024
  with self.assertRaises(AssertionError):compare(a,b)
  b=result([False,True])
  with self.assertRaises(AssertionError):compare(a,b)
 def test_fresh_size_and_retention_gates_and_paired_statistics(self):
  a=result([True]*100);b=result([False]*100)
  r=compare(a,b,fresh=True,controls_preserved=True,bootstrap_samples=1000)
  self.assertEqual(r['delta_pp'],100);self.assertEqual(r['ci95_pp'],[100,100]);self.assertLess(r['one_sided_p'],.05)
  self.assertTrue(r['coding_superiority_confirmed'])
  self.assertFalse(compare(a,b,fresh=False,controls_preserved=True,bootstrap_samples=100)['coding_superiority_confirmed'])
  self.assertFalse(compare(a,b,fresh=True,controls_preserved=False,bootstrap_samples=100)['coding_superiority_confirmed'])
  self.assertFalse(compare(result([True]*5),result([False]*5),fresh=True,controls_preserved=True,bootstrap_samples=100)['coding_superiority_confirmed'])

if __name__=='__main__':unittest.main()
