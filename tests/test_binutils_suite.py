"""The documented profiler exception must never mask incomplete/other suites."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('binutils_evaluation', ROOT / 'scripts/build/h07/evaluate-binutils.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)
GPROF = '# TOTAL: 3\n# PASS: 3\n# FAIL: 0\n# ERROR: 0\n'


class BinutilsSuite(unittest.TestCase):
    def reports(self):
        reports = {}
        for name, count in evaluation.SUITES.items():
            reports[name] = ''.join(f'PASS: test-{n}\n' for n in range(count)) + f'=== suite Summary ===\n# of expected passes {count}\n'
        reports['gprofng/gprofng.sum'] += 'FAIL: tmpdir/gp-gmon\n'
        return reports

    def test_only_documented_failure_with_complete_reports_accepted(self):
        self.assertTrue(evaluation.classify(self.reports(), 2, GPROF)['accepted'])
        self.assertFalse(evaluation.classify(self.reports(), 143, GPROF)['accepted'])

    def test_missing_or_truncated_suite_rejected(self):
        reports = self.reports()
        reports['ld/ld.sum'] = 'PASS: one\n'
        self.assertFalse(evaluation.classify(reports, 2, GPROF)['accepted'])
        reports.pop('gas/testsuite/gas.sum')
        self.assertFalse(evaluation.classify(reports, 2, GPROF)['accepted'])

    def test_unexplained_failure_or_missing_gprof_rejected(self):
        reports = self.reports()
        reports['ld/ld.sum'] += 'FAIL: executable-security-regression\n'
        self.assertFalse(evaluation.classify(reports, 2, GPROF)['accepted'])
        self.assertFalse(evaluation.classify(self.reports(), 2, '')['accepted'])
