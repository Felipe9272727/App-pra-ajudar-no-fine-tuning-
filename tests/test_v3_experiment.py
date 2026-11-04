import inspect
from pathlib import Path
import sys
import unittest
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v3_experiment'))
from codec import load_codec,bytes_tensor,LEVELS,WIDTH,DIM
from runtime import NCMExperiment,exact_grade,HERE


class V3ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.codec=load_codec(HERE/'codec.pt')

    def test_official_quantizer_roundtrip_matches_incremental_levels(self):
        ids=torch.stack([bytes_tensor('Ab12'),bytes_tensor('907'),bytes_tensor('deed')])
        codes=self.codec.vq.z_to_idx(self.codec.continuous(ids))
        expected=self.codec.vq.idx_to_zhats(codes,return_zlevels=False)[0][-1]
        z=torch.zeros(len(ids),WIDTH,DIM);offset=0
        for i,size in enumerate(LEVELS):
            z=self.codec.update(z,codes[:,offset:offset+size],i);offset+=size
        self.assertTrue(torch.equal(z,expected))
        self.assertEqual(self.codec.text(z[1]),'907')

    def test_case_is_not_erased_by_string_grading(self):
        row={'answer':'ABC','numeric':False}
        self.assertEqual(exact_grade('ABC',row),(True,True))
        self.assertEqual(exact_grade('abc',row),(False,False))

    def test_generation_interface_accepts_no_gold_answer(self):
        self.assertEqual(list(inspect.signature(NCMExperiment.generate).parameters),['self','question'])

    def test_codec_length_limit_is_explicit(self):
        with self.assertRaises(ValueError):bytes_tensor('123456789')


if __name__=='__main__':unittest.main()
