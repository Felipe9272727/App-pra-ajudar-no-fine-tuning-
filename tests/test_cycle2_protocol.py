import importlib.util
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab_rsi'))
from protocol import grade,first_error,validation_passes
from publish_progress import allowed

class Cycle2Tests(unittest.TestCase):
    def test_case_sensitive_string_tasks(self):
        row={'answer':'ABCDE','numeric':False,'case_sensitive':True}
        self.assertEqual(grade('abcde',row),(False,False))
        self.assertEqual(grade('ABCDE',row),(True,True))
        self.assertEqual(grade('Paris',{'answer':'paris','numeric':False}),(True,True))

    def test_first_error_including_stop(self):
        self.assertEqual(first_error([4,6,7],[4,5,7]),1)
        self.assertEqual(first_error([4,5,9],[4,5,0]),2)
        self.assertIsNone(first_error([4,5,0],[4,5,0]))

    def test_promotion_requires_actual_gain_and_no_control_loss(self):
        baseline={'exact_correct':10,'rows':[{'numeric':False,'exact_correct':True}]}
        r={'exact_correct':10,'rows':baseline['rows']}
        self.assertFalse(validation_passes(r,baseline))
        r['exact_correct']=11
        self.assertTrue(validation_passes(r,baseline))
        r['rows']=[{'numeric':False,'exact_correct':False}]
        self.assertFalse(validation_passes(r,baseline))

    def test_guard_excludes_source_data_and_unrelated_files(self):
        for p in ['lab_rsi/candidate_01.pt','lab_rsi/round_001.json','lab_rsi/archive.json','LAB_REPORT.md']:
            self.assertTrue(allowed(p),p)
        for p in ['lab_rsi/data.json','lab_rsi/ci.py','lab_rsi/ci_run_request.json','AGENTS.md','.github/workflows/liquid-sense-rsi-cycle2.yml','lab_rsi/candidate_04.pt']:
            self.assertFalse(allowed(p),p)

    def test_new_questions_disjoint_from_prior_questions(self):
        def questions(obj):
            if isinstance(obj,dict):
                out={obj['question'].strip()} if 'question' in obj else set()
                for v in obj.values():out|=questions(v)
                return out
            if isinstance(obj,list):
                out=set()
                for v in obj:out|=questions(v)
                return out
            return set()
        data=json.loads((ROOT/'lab_rsi/data.json').read_text());seen=set()
        for p in list((ROOT/'history').glob('*data*.json'))+[ROOT/'v2_adaptation/data_v2.json']+list((ROOT/'rsi').glob('*.json')):
            seen|=questions(json.loads(p.read_text()))
        for split,count in [('train',224),('development',24),('validation',32),('heldout',80)]:
            q=questions(data[split]);self.assertEqual(len(q),count)
            self.assertFalse(q&seen,split);seen|=q

if __name__=='__main__':unittest.main()
