"""Small record tests are not evidence of a complete native qualification."""
import copy
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/build'))
import db_standard_diagnostics as diagnostics
from db_standard_qualify import DECISION, stable_proof, validate_qualification


class ExactQualificationBoundary(unittest.TestCase):
    def fixture(self):
        output = 'unit-only native-output binding\n'
        diagnostic = {'classification_complete': True, 'actual_failures': [], 'unclassified': [],
                      'exact_diagnostic_profile': True, 'informational_count': 13, 'unexpected_count': 23,
                      'coverage_warning_counts': {name: 1 for name in diagnostics.COVERAGE_TYPES},
                      'outer_headers': len(diagnostics.HEADERS), 'suite_accepted': False,
                      'package_accepted': False, 'native_exit': 0, 'original_reports_unchanged': True,
                      'checker_stdout_sha256': hashlib.sha256(output.encode()).hexdigest(),
                      'native_command': ['unit-only-path'], 'checker_sha256': 'unit-only-script'}
        review = {'review_complete': True, 'raw_driver_exit': 1, 'raw_test_exit': 1,
                  'suite_accepted': False, 'package_accepted': False, 'custody_sealed': False,
                  'diagnostics': diagnostic,
                  'coverage': {'custody_sealed': True, 'coverage_witness_verified': True, 'fixture': 'unit-only'},
                  'execution': {'execution_evidence_verified': True}}
        proof = stable_proof(review)
        record = {'decision': DECISION, 'standard_suite_qualified': True, 'package_accepted': False,
                  'raw_driver_exit': 1, 'raw_test_exit': 1, 'raw_upstream_summary': 'Regression Tests Failed',
                  'source_custody_sha256': 'unit-only-custody', 'proof': proof, 'review': review,
                  'coverage_fixture': 'unit-only', 'native_checker_stdout': output}
        return review, proof, record

    def test_real_failures_incomplete_reviews_and_unprotected_witnesses_refuse(self):
        review, _, _ = self.fixture()
        cases = [((), 'raw_test_exit', 0), ((), 'raw_driver_exit', True), ((), 'review_complete', False),
                 (('coverage',), 'custody_sealed', False), (('execution',), 'execution_evidence_verified', False),
                 (('diagnostics',), 'actual_failures', ['FAIL: real assertion']),
                 (('diagnostics',), 'unclassified', ['unknown diagnostic']),
                 (('diagnostics',), 'unexpected_count', 24), (('diagnostics',), 'native_exit', False)]
        for path, key, value in cases:
            changed = copy.deepcopy(review)
            target = changed
            for part in path:
                target = target[part]
            target[key] = value
            with self.subTest(path=path, key=key), self.assertRaises(ValueError):
                stable_proof(changed)

    def test_raw_outcomes_output_and_custody_remain_bound(self):
        review, proof, record = self.fixture()
        validate_qualification(record, proof, 'unit-only-custody')
        changed = copy.deepcopy(review)
        changed['diagnostics']['native_command'] = ['another-private-checker-path']
        changed['diagnostics']['checker_sha256'] = 'path-dependent-script'
        self.assertEqual(stable_proof(changed), proof)
        for key, value in [('raw_test_exit', 0), ('raw_driver_exit', True),
                           ('raw_upstream_summary', 'Regression Tests Succeeded'),
                           ('package_accepted', True), ('native_checker_stdout', 'changed output'),
                           ('coverage_fixture', 'different witness'), ('source_custody_sha256', 'changed'),
                           ('decision', 'generic warning waiver')]:
            altered = copy.deepcopy(record)
            altered[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_qualification(altered, proof, 'unit-only-custody')
