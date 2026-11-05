"""Numerical invariants matter when editing48 parameter tensors together."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reasoning/multi008'))
from study008 import torch,corrected_vector,aggregate

class MultiTensorCalibrationTests(unittest.TestCase):
    def test_zero_correction_preserves_exact_weights(self):
        w=torch.tensor([-1.5,-1.,-.5,0.,1e-7,.25,1.],dtype=torch.bfloat16)
        new,_=corrected_vector(w,torch.zeros_like(w,dtype=torch.float32))
        self.assertTrue(torch.equal(w,new))

    def test_zero_centered_gain_direction_sign_and_quantized_bound(self):
        w=torch.tensor([-1.5,-1.,-.5,0.,1.],dtype=torch.bfloat16)
        new,_=corrected_vector(w,torch.full_like(w,.02,dtype=torch.float32))
        self.assertEqual(float(new[1]),-1.)
        gain=1+w.float();actual=1+new.float();valid=gain.abs()>1e-6
        ratio=actual[valid]/gain[valid]
        self.assertTrue(bool((ratio>=1).all()))
        self.assertTrue(bool(((ratio-1).abs()<=.03).all()))
        self.assertTrue(bool((gain[valid]*actual[valid]>0).all()))
        self.assertAlmostEqual(float(actual[2]),.5*torch.tensor(.02).exp().item(),delta=.003)

    def test_episode_mean_does_not_weight_long_rollouts_more(self):
        episodes={'short':{'moments':{'x':torch.tensor([1.,4.])}},
                  'long':{'moments':{'x':torch.tensor([9.,16.])}}}
        self.assertTrue(torch.equal(aggregate(episodes)['x'],torch.tensor([5.,10.])))

if __name__=='__main__':unittest.main()
