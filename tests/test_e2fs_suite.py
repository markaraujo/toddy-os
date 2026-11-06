"""Only the measured allocation-count incompatibility can be qualified."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('e2fs_suite',Path(__file__).resolve().parents[1]/'scripts/build/h07/evaluate-e2fs.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)
class E2fsSuite(unittest.TestCase):
    def fixture(self):return ['393 tests succeeded\t1 tests failed\nTests failed: m_assume_storage_prezeroed ',['m_assume_storage_prezeroed.failed'],'> 10000\n232\n','> 10000\n224\n',2]
    def test_qualified_result_retains_native_obligation(self):
        result=suite.evaluate(*self.fixture());self.assertFalse(result['all_pass']);self.assertTrue(result['installed_ext4_roundtrip_required'])
    def test_different_failure_or_incomplete_suite_rejected(self):
        for index,value in [(0,'392 tests succeeded\t2 tests failed'),(1,['m_other.failed']),(2,'> 10000\n0\n'),(4,137)]:
            args=self.fixture();args[index]=value
            with self.assertRaises(ValueError):suite.evaluate(*args)
if __name__=='__main__':unittest.main()
