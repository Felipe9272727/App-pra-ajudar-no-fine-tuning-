import sys,unittest
from pathlib import Path
from types import SimpleNamespace
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from loop012.core import BypassSecond,style_metrics
from loop012.edit import protected_fit,ForceStudentPrefix

class LoopSpecializationTests(unittest.TestCase):
 def test_bypass_returns_first_exit_without_mutating_either_tensor(self):
  layer=SimpleNamespace(_last_native_visit=0);model=SimpleNamespace(model=SimpleNamespace(language_model=SimpleNamespace(layers=[None]*27+[layer])))
  b=BypassSecond(model);x=torch.tensor([1.,2.]);y=torch.tensor([8.,9.]);self.assertIsNone(b.hook(layer,(),x));layer._last_native_visit=1
  got=b.hook(layer,(),y);self.assertTrue(torch.equal(got,x));got[0]=100.;self.assertEqual(float(x[0]),1.);self.assertEqual(float(y[0]),8.)
 def test_protected_update_is_orthogonal_to_preservation_inputs(self):
  W=torch.ones(3,8);P=torch.eye(8)[:3];X=torch.eye(8)[3:5];D=torch.ones(2,3)*.01
  update,info=protected_fit(W,P,X,D);self.assertIsNotNone(update);self.assertLess(float((P@update.T).abs().max()),1e-6)
  self.assertLess(float((X@update.T-D).norm()),float(D.norm()));self.assertLessEqual(float(update.norm()/W.norm()),.020001)
 def test_unidentifiable_target_aborts_instead_of_uncontrolled_update(self):
  W=torch.ones(2,4);P=torch.eye(4);X=P[:2];D=torch.ones(2,2)
  update,info=protected_fit(W,P,X,D);self.assertIsNone(update);self.assertIn('abort',info)
 def test_teacher_prefix_only_forces_preexisting_student_ids(self):
  p=ForceStudentPrefix(torch.tensor([3,5]),2);scores=torch.arange(10.).view(1,-1)
  self.assertEqual(int(p(torch.tensor([[1,2]]),scores).argmax()),3)
  self.assertEqual(int(p(torch.tensor([[1,2,3]]),scores).argmax()),5)
  self.assertTrue(torch.equal(p(torch.tensor([[1,2,3,5]]),scores),scores))
 def test_language_structure_is_checked_independently_of_length(self):
  self.assertTrue(style_metrics('Cache guarda dados. Isso evita repetir trabalho.','explain_cache_pt')['structural_instruction_pass'])
  self.assertFalse(style_metrics('Cache guarda dados.','explain_cache_pt')['structural_instruction_pass'])
  self.assertTrue(style_metrics('{"nome":"caderno","quantidade":3,"disponivel":true}','structured_pt')['structural_instruction_pass'])
  self.assertFalse(style_metrics('```json\n{}\n```','structured_pt')['structural_instruction_pass'])

if __name__=='__main__':unittest.main()
