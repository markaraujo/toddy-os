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

# Tcl make test may exit zero despite a failed test, unlike Automake check.
tcl_spec=importlib.util.spec_from_file_location('tcl_evaluation',ROOT/'scripts/build/h07/evaluate-tcl.py')
tcl_evaluation=importlib.util.module_from_spec(tcl_spec)
tcl_spec.loader.exec_module(tcl_evaluation)


class TclSuite(unittest.TestCase):
    def test_extension_summaries_cannot_hide_missing_core_suite(self):
        self.assertFalse(tcl_evaluation.classify(
            'all.tcl: Total 793 Passed 727 Skipped 66 Failed 0\n')['accepted'])

    def test_zero_exit_does_not_hide_test_failure(self):
        self.assertFalse(tcl_evaluation.classify(
            'all.tcl: Total 30000 Passed 29998 Skipped 1 Failed 1\n')['accepted'])
        self.assertTrue(tcl_evaluation.classify(
            'all.tcl: Total 30000 Passed 29999 Skipped 1 Failed 0\n')['accepted'])

    def test_only_exact_missing_optional_database_clients_are_classified(self):
        core = 'all.tcl: Total 30000 Passed 29999 Skipped 1 Failed 0\n'
        optional = 'Test file error: couldn\'t load file "libpq.so.5": libpq.so.5: cannot open shared object file: No such file or directory\n'
        self.assertTrue(tcl_evaluation.classify(core + optional)['accepted'])
        self.assertFalse(tcl_evaluation.classify(core + optional.replace('libpq.so.5', 'libtcl8.6.so'))['accepted'])


if __name__=='__main__':
    unittest.main()
