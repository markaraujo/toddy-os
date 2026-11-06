"""Reject novel or incomplete Tar failures while retaining the raw known result."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('tar_suite',Path(__file__).resolve().parents[1]/'scripts/build/h07/evaluate-tar.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)

class TarSuite(unittest.TestCase):
    def fixture(self):
        skipped=set(range(1,21))
        output='\n'.join(f'{n}: group '+('skipped (test:1)' if n in skipped else 'FAILED (capabs_raw01.at:28)' if n==233 else 'ok') for n in range(1,245))
        output+='\nERROR: 224 tests were run,\n1 failed unexpectedly.\n20 tests were skipped.\n'
        detail='--- expected\n+++ actual\n@@ -1,2 +1,2 @@\n-dir/file = cap_chown=ei\n+dir/file cap_chown=ei\nFAILED (capabs_raw01.at:28)'
        return output,detail
    def test_known_output_is_explicitly_not_all_pass(self):
        result=suite.evaluate(*self.fixture(),2)
        self.assertEqual((result['pass'],result['skip'],result['known_format_failures']),(223,20,[233]))
        self.assertFalse(result['all_pass'])
    def test_new_capability_loss_rejected(self):
        output,detail=self.fixture()
        with self.assertRaisesRegex(ValueError,'Unknown capability'):
            suite.evaluate(output,detail.replace('+dir/file cap_chown=ei','+dir/file'),2)
    def test_incomplete_duplicate_and_new_failure_rejected(self):
        output,detail=self.fixture()
        for changed in [output.replace('244: group ok',''),output+'\n244: group ok',output.replace('234: group ok','234: group FAILED (other:1)')]:
            with self.assertRaises(ValueError):suite.evaluate(changed,detail,2)
    def test_crashed_make_rejected(self):
        with self.assertRaises(ValueError):suite.evaluate(*self.fixture(),137)

if __name__=='__main__':unittest.main()
