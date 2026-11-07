"""Parser fixtures exercise rejection logic; they are not native suite results."""
import importlib.util
from pathlib import Path
import sys
import unittest

BUILD = Path(__file__).resolve().parents[1] / 'scripts/build'
sys.path.insert(0, str(BUILD))
spec = importlib.util.spec_from_file_location('db_diagnostics', BUILD / 'db_standard_diagnostics.py')
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


class DiagnosticReconciliation(unittest.TestCase):
    def fixture(self, extra=()):
        start = 'Test suite run started at: 01:00 11/07/2026'
        end = 'Test suite run completed at: 02:00 11/07/2026'
        unexpected = [diag.INFORMATIONAL] * 4 + list(diag.WARNINGS) + [diag.INFORMATIONAL] * 9 + list(extra)
        checker = ['UNEXPECTED OUTPUT: ' + line for line in unexpected]
        report = '\n'.join([start, diag.VERSION, *unexpected, 'Regression Tests Failed', end]) + '\n'
        stdout = '\n'.join([start, diag.VERSION, *diag.HEADERS, *checker,
                            'Regression Tests Failed', 'Check UNEXPECTED OUTPUT lines.',
                            'Review ALL.OUT.x for details.', end,
                            'Complete DB regression summary failed']) + '\n'
        return report, stdout, '\n'.join(checker + ['TODDY_CHECK_RESULT 1']) + '\n'

    def test_exact_profile_is_classification_only(self):
        report = diag.classify(*self.fixture())
        diag.require_diagnostic_profile(report)
        self.assertFalse(report['suite_accepted'])
        self.assertFalse(report['package_accepted'])
        self.assertEqual(report['raw_summary'], 'Regression Tests Failed')

    def test_actual_failures_unknown_diagnostics_and_changed_counts_remain_rejected(self):
        for line in ('FAIL: actual assertion', 'FAIL: ' + diag.INFORMATIONAL,
                     'WARNING: log record type __new: not tested', diag.INFORMATIONAL,
                     'arbitrary new output', diag.WARNINGS[0]):
            with self.subTest(line=line):
                report = diag.classify(*self.fixture([line]))
                with self.assertRaises(ValueError):
                    diag.require_diagnostic_profile(report)

    def test_truncation_filtered_reports_and_fabricated_outer_output_are_rejected(self):
        report, stdout, checker = self.fixture()
        cases = [
            (report.rsplit('\n', 2)[0], stdout, checker),
            (report + 'unexplained trailing output\n', stdout, checker),
            (report, stdout.replace(diag.HEADERS[3] + '\n', ''), checker),
            (report, stdout + 'unexplained output\n', checker),
            (report, stdout.replace('UNEXPECTED OUTPUT: ' + diag.WARNINGS[0] + '\n', ''), checker),
            (report, stdout, checker.replace('TODDY_CHECK_RESULT 1', 'TODDY_CHECK_RESULT 0')),
            (report, stdout, checker + 'extra\n'),
            ('FAIL: injected assertion\n' + report, stdout, checker),
            (report.replace('Regression Tests Failed', 'Regression Tests Succeeded'), stdout, checker),
        ]
        for values in cases:
            with self.subTest(values=values), self.assertRaises(ValueError):
                diag.classify(*values)
