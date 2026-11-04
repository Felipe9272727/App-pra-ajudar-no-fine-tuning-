import importlib.util
from pathlib import Path
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('watchdog', ROOT/'rsi100/watchdog.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)

class WatchdogTests(unittest.TestCase):
    def test_stale_journal_cannot_reset_startup_deadline(self):
        self.assertTrue(w.expired({'attempt':'old'}, 'new', 400, 0))
        self.assertFalse(w.expired({'attempt':'old'}, 'new', 10, 0))

    def test_phase_deadline(self):
        e = {'attempt':'current','started_unix':10,'budget_seconds':20}
        self.assertFalse(w.expired(e,'current',29,0))
        self.assertTrue(w.expired(e,'current',31,0))

    def test_success_and_failure_passthrough(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'missing.json'
            self.assertEqual(w.supervise([sys.executable,'-c','pass'],p,poll=.02),0)
            self.assertEqual(w.supervise([sys.executable,'-c','raise SystemExit(7)'],p,poll=.02),7)

    def test_stalled_worker_is_stopped(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(w.supervise([sys.executable,'-c','import time; time.sleep(20)'],Path(d)/'missing.json',poll=.02,startup_budget=.1),124)
