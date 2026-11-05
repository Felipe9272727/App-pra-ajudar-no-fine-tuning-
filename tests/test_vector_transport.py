"""Protected closed-form correction invariants before touching real weights."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reasoning/multi009'))
from study009 import fit_delta,torch

class VectorTransportTests(unittest.TestCase):
    def test_protected_span_stays_null_and_code_moves_in_target_direction(self):
        base=torch.ones((2,4))
        language=torch.tensor([[1.,0.,0.,0.],[0.,1.,0.,0.]])
        code=torch.tensor([[1.,0.,1.,0.],[0.,1.,0.,1.]])
        desired=torch.tensor([[1.,0.],[0.,1.]])
        delta,info=fit_delta(base,language,code,desired)
        self.assertIsNotNone(delta)
        self.assertLess(float((language@delta.T).abs().max()),1e-7)
        self.assertGreater(float(((code@delta.T)*desired).sum()),0.)
        self.assertLessEqual(float(delta.norm()/base.norm()),.00200001)

    def test_no_unprotected_direction_aborts(self):
        language=torch.eye(4);code=torch.ones((2,4));base=torch.ones((2,4))
        delta,info=fit_delta(base,language,code,torch.ones((2,2)))
        self.assertIsNone(delta);self.assertIn('abort',info)

if __name__=='__main__':unittest.main()
