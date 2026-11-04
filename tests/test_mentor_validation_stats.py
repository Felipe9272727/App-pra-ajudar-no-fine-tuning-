"""Known paired-test probabilities: correlated cases are not extra samples."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1]/'mentor/validation_004/summarize.py'
spec = importlib.util.spec_from_file_location('mentor_validation_summary', path)
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)


class PairedStatisticsTests(unittest.TestCase):
    def report(self, bits):
        return {'rows':[{'id':str(i),'group':'far','all_passed':b,
                         'output':str(b),'case_passed':[b]*8}
                        for i,b in enumerate(bits)]}

    def test_six_task_wins_are_six_trials_despite_48_case_wins(self):
        result = summary.compare(self.report([False]*24), self.report([True]*6+[False]*18))
        self.assertEqual(len(result['case_wins']), 48)
        self.assertEqual(len(result['task_wins']), 6)
        self.assertEqual(result['exact_two_sided_mcnemar_p'], 1/32)

    def test_single_win_is_insufficient_and_identical_is_not_improvement(self):
        same = self.report([True]*24)
        self.assertEqual(summary.compare(same,same)['exact_two_sided_mcnemar_p'], 1.)
        result = summary.compare(self.report([False]*24),self.report([True]+[False]*23))
        self.assertEqual(result['exact_two_sided_mcnemar_p'], 1.)


if __name__ == '__main__':
    unittest.main()
