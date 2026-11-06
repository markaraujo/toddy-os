"""Known chroot exceptions cannot absorb new native service failures."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('systemd_suite',Path(__file__).resolve().parents[1]/'scripts/build/h07/evaluate-systemd.py')
suite=importlib.util.module_from_spec(spec);spec.loader.exec_module(suite)
class SystemdSuite(unittest.TestCase):
    def fixture(self):
        rows=[{'name':f'test-{i}','result':'OK','returncode':0} for i in range(1862)]
        rows[0]={'name':'core - systemd:test-namespace','result':'FAIL','returncode':-6,'stderr':'/* test_process_is_owned_by_uid */\nsrc/test/test-namespace.c:391: Assertion failed: Expected "r" to succeed, but got error: -1/EPERM'}
        return rows
    def test_known_chroot_failure_retains_native_obligation(self):
        r=suite.evaluate(self.fixture(),1)
        self.assertFalse(r['all_pass']);self.assertTrue(r['native_namespace_retest_required_before_G1'])
    def test_novel_failure_cause_or_identity_is_rejected(self):
        for key,value in [('name','test-new'),('stderr','different assertion'),('returncode',1)]:
            rows=self.fixture();rows[0][key]=value
            with self.assertRaises(ValueError):suite.evaluate(rows,1)
    def test_incomplete_duplicate_and_timeout_are_rejected(self):
        rows=self.fixture()
        for changed in [rows[:-1],rows[:-1]+[rows[-2]],rows[:-1]+[dict(rows[-1],result='TIMEOUT')]]:
            with self.assertRaises(ValueError):suite.evaluate(changed,1)
if __name__=='__main__':unittest.main()
