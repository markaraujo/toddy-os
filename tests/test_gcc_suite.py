"""Pinned reference exceptions must not hide a novel or incomplete GCC result."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('gcc_evaluation', Path(__file__).resolve().parents[1] / 'scripts/build/h07/evaluate-gcc.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class GccSuite(unittest.TestCase):
    def passing(self):
        return 'PASS: one\nPASS: two\n=== gcc Summary ===\n# of expected passes 2\n'

    def test_exact_reference_outcome_is_classified_but_new_failure_is_rejected(self):
        known = 'FAIL: gcc.target/i386/known.c scan-assembler known-pattern'
        self.assertTrue(evaluation.classify({'gcc': self.passing() + known}, known, 2, {'gcc': 2})['accepted'])
        self.assertFalse(evaluation.classify({'gcc': self.passing() + known + '\nFAIL: security/regression.c'}, known, 2, {'gcc': 2})['accepted'])
        self.assertFalse(evaluation.classify({'gcc': self.passing() + known.replace('known-pattern', 'execution failure')}, known, 2, {'gcc': 2})['accepted'])

    def test_incomplete_or_interrupted_suite_cannot_use_exception(self):
        self.assertFalse(evaluation.classify({'gcc': 'PASS: one\n'}, '', 0, {'gcc': 2})['accepted'])
        self.assertFalse(evaluation.classify({'gcc': self.passing()}, '', 143, {'gcc': 2})['accepted'])
        self.assertFalse(evaluation.classify({'gcc': self.passing()}, '', 0, {'gcc': 3})['accepted'])
        self.assertFalse(evaluation.classify({}, '', 0, {'gcc': 2})['accepted'])

    def test_unknown_unexpected_success_or_error_is_rejected(self):
        for status in ['XPASS', 'UNRESOLVED', 'ERROR']:
            self.assertFalse(evaluation.classify({'gcc': self.passing() + status + ': unclassified'}, '', 0, {'gcc': 2})['accepted'])
