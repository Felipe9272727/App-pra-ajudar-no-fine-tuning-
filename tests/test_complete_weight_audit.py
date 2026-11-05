import hashlib
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native010'))
import audit_all as scanner
from audit_all import torch,inspect_tensor

class CompleteWeightAuditTests(unittest.TestCase):
    def test_streaming_covers_every_value_and_hash(self):
        old=scanner.CHUNK;scanner.CHUNK=3
        try:
            x=torch.tensor([[0.,-2.,1.],[3.,-4.,5.]],dtype=torch.bfloat16).T
            result=inspect_tensor(x)
        finally:scanner.CHUNK=old
        self.assertEqual(result['numel'],6);self.assertEqual(result['finite'],6)
        self.assertEqual(result['zeros'],1);self.assertEqual(result['negative'],2)
        self.assertEqual(sum(result['magnitude_histogram']),6)
        self.assertAlmostEqual(result['mean'],.5)
        self.assertEqual(result['sha256_values'],hashlib.sha256(x.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())

    def test_nonfinite_values_are_counted_without_losing_rest_of_audit(self):
        x=torch.tensor([float('nan'),float('inf'),float('-inf'),0.,-1.])
        result=inspect_tensor(x,reference=torch.zeros(5))
        self.assertEqual((result['finite'],result['nan'],result['inf']),(2,1,2))
        self.assertEqual(sum(result['magnitude_histogram']),2)
        self.assertEqual(result['source_difference']['finite_value_pairs'],2)

    def test_extended_convolution_alignment(self):
        original=torch.tensor([[[1.,2.,3.,4.]]])
        current=torch.tensor([[[.5,0.,0.,1.,2.,3.,4.]]])
        result=inspect_tensor(current,conv_reference=original)
        self.assertEqual(result['source_difference']['compared_values'],7)
        self.assertEqual(result['source_difference']['changed_values'],1)
        self.assertAlmostEqual(result['source_difference']['l2'],.5)

    def test_full_matrix_power_and_norms(self):
        x=torch.tensor([[3.,0.],[0.,0.]])
        norms,info=scanner.matrix_diagnostics(x)
        self.assertTrue(torch.equal(norms['row_norms'],torch.tensor([3.,0.])))
        self.assertEqual(info['zero_columns'],1)
        self.assertAlmostEqual(info['spectral_norm_power_estimate'],3.,places=5)
        self.assertAlmostEqual(info['stable_rank_upper_estimate'],1.,places=5)

    def test_dispatch_sees_parameter_read_through_transpose_view(self):
        p=torch.nn.Parameter(torch.ones(2,3),requires_grad=False)
        trace=scanner.WeightAccess([('projection',p)])
        with trace:output=torch.ones(1,3)@p.T
        self.assertEqual(output.tolist(),[[3.,3.]])
        self.assertGreater(sum(trace.reads['projection'].values()),0)

if __name__=='__main__':unittest.main()
