import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'lab_rsi'))
from ci_merge import merge_shards


class CheckpointTests(unittest.TestCase):
    def parts(self):
        base={'variant':'baseline','data_sha256':'data','patch_sha256':None,
            'frozen_selection_sha256':'frozen','inference_code_sha256':{'file':'code'},
            'protocol':{'threads':4},'loaded_parameters':1020252592,'shards':2,
            'status':'complete','peak_rss_mib':2500}
        return [{**copy.deepcopy(base),'shard':i,'rows':[
            {'id':f'q{j}','exact_correct':j%2==0,'content_correct':True} for j in range(i,4,2)]} for i in range(2)]

    def test_complete_partition_reconstructs_original_order(self):
        merged=merge_shards(self.parts(),['q0','q1','q2','q3'])
        self.assertEqual([r['id'] for r in merged['rows']],['q0','q1','q2','q3'])
        self.assertEqual((merged['exact_correct'],merged['content_correct'],merged['total']),(2,4,4))

    def test_rejects_mixed_weights_code_data_and_protocol(self):
        for field in ['patch_sha256','frozen_selection_sha256','data_sha256','inference_code_sha256','protocol']:
            with self.subTest(field=field):
                parts=self.parts();parts[1][field]='wrong'
                with self.assertRaises(ValueError):merge_shards(parts,['q0','q1','q2','q3'])

    def test_rejects_repeated_or_missing_questions(self):
        parts=self.parts();parts[1]['rows'][0]['id']='q0'
        with self.assertRaises(ValueError):merge_shards(parts,['q0','q1','q2','q3'])
        parts=self.parts();parts[1]['rows'].pop()
        with self.assertRaises(ValueError):merge_shards(parts,['q0','q1','q2','q3'])

    def test_rejects_partial_or_missing_shards(self):
        parts=self.parts();parts[1]['status']='running'
        with self.assertRaises(ValueError):merge_shards(parts,['q0','q1','q2','q3'])
        with self.assertRaises(ValueError):merge_shards(self.parts()[:1],['q0','q1','q2','q3'])

    def test_rejects_absent_metadata(self):
        parts=self.parts();del parts[1]['frozen_selection_sha256']
        with self.assertRaises(ValueError):merge_shards(parts,['q0','q1','q2','q3'])


if __name__=='__main__':unittest.main()
