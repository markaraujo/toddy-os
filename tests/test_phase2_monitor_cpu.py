from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/host'))
from phase2_monitor import cpu_progress


class CpuProgressTests(unittest.TestCase):
    def test_finished_compiler_does_not_cancel_new_compiler_progress(self):
        _,before=cpu_progress({1:(0,10,1),2:(1,10000,2)},{1,2},{})
        delta,after=cpu_progress({1:(0,10,1),3:(1,100,3)},{1,3},before)
        self.assertEqual(delta,100)
        self.assertEqual(set(after),{(1,1),(3,3)})

    def test_reused_pid_has_new_start_identity(self):
        delta,_=cpu_progress({2:(1,15,999)},{2},{(2,123):500})
        self.assertEqual(delta,15)

    def test_unchanged_process_is_not_progress(self):
        delta,_=cpu_progress({2:(1,500,123)},{2},{(2,123):500})
        self.assertEqual(delta,0)
