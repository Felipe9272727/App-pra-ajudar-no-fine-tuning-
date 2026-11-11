import unittest
from core import *
from judge import evaluate

class Tests(unittest.TestCase):
    def test_sphere_margin(self):
        h=torch.zeros(2,1024);h[:,0]=1;h[:,1]=3
        a=torch.zeros_like(h);a[:,0]=-1
        z=rotate_to_margin(h,a,.5)
        self.assertTrue(torch.allclose(h.norm(dim=-1),z.norm(dim=-1),atol=1e-6))
        margin=(z*a).sum(-1)/z.square().mean(-1).sqrt()
        self.assertTrue(bool((margin>=.49999).all()))
    def test_satisfied_halfspace_identity(self):
        h=torch.ones(2,1024);a=h.clone()
        self.assertTrue(torch.equal(h,rotate_to_margin(h,a,.5)))
    def test_underscore_valid_and_tests_separate(self):
        row={'benchmark':'mbpp','tests':['assert f([2,3]) == [1,1]'],'test_imports':[],'entry_point':'f'}
        self.assertTrue(evaluate('def f(xs): return [1 for _ in xs]',row)['all_passed'])
        self.assertFalse(evaluate('def f(xs): return []\ndef check(*args): return True',row)['all_passed'])
    def test_import_and_filesystem_rejected(self):
        row={'benchmark':'mbpp','tests':['assert f([])==[]'],'test_imports':[],'entry_point':'f'}
        self.assertFalse(evaluate('import os\ndef f(xs): return []',row)['all_passed'])
        self.assertFalse(evaluate('def f(xs): return open("/etc/hostname").read()',row)['all_passed'])

if __name__=='__main__':unittest.main()
