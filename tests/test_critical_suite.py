"""Critical-suite acceptance must reject truncated, interrupted or failing runs."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('glibc_evaluation',ROOT/'scripts/build/h07/evaluate-glibc.py')
evaluation=importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class CriticalSuite(unittest.TestCase):
    def passing(self):
        return [f'PASS: test/{n}' for n in range(6000)]

    def test_unexplained_failure_rejected_even_with_zero_exit(self):
        record=evaluation.classify(self.passing()+['FAIL: security/regression'],0)
        self.assertFalse(record['accepted'])
        self.assertEqual(record['unexplained_failures'],['security/regression'])

    def test_interruption_cannot_use_known_exception_as_success(self):
        record=evaluation.classify(self.passing()+['FAIL: io/tst-lchmod'],143)
        self.assertFalse(record['accepted'])

    def test_truncated_or_entirely_unsupported_run_rejected(self):
        self.assertFalse(evaluation.classify(self.passing()[:20],0)['accepted'])
        self.assertFalse(evaluation.classify(['UNSUPPORTED: test']*6000,0)['accepted'])

    def test_documented_chroot_exception_is_explicit(self):
        record=evaluation.classify(self.passing()+['FAIL: io/tst-lchmod'],2)
        self.assertTrue(record['accepted'])
        self.assertEqual(set(record['expected_failures']),{'io/tst-lchmod'})


if __name__=='__main__':
    unittest.main()
