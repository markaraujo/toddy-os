"""Bash run-all's unconditional zero exit cannot substitute for test evidence."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('bash_evaluation', Path(__file__).resolve().parents[1] / 'scripts/build/h07/evaluate-bash.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


class BashSuite(unittest.TestCase):
    def test_differences_are_rejected_even_with_all_test_headers(self):
        expected = {f'run-{n}' for n in range(60)}
        full = '\n'.join(sorted(expected))
        self.assertTrue(evaluation.classify(full, expected)['accepted'])
        self.assertFalse(evaluation.classify(full + '\n< unexpected output\n', expected)['accepted'])
        self.assertFalse(evaluation.classify(full + '\n> unexpected expected-output mismatch\n', expected)['accepted'])

    def test_missing_or_truncated_test_coverage_is_rejected(self):
        expected = {f'run-{n}' for n in range(60)}
        self.assertFalse(evaluation.classify('\n'.join(sorted(expected)[:-1]), expected)['accepted'])
        self.assertFalse(evaluation.classify('run-one\n', {'run-one'})['accepted'])

    def test_only_complete_exact_group_specific_exceptions_are_accepted(self):
        expected = {f'run-{n}' for n in range(60)}
        full = '\n'.join(sorted(expected))
        known = {'run-9': ['< known actual', '> known reference']}
        # run-9 sorts last, so this diff belongs to exactly that group.
        self.assertTrue(evaluation.classify(full+'\n< known actual\n> known reference\n',expected,known)['accepted'])
        self.assertFalse(evaluation.classify(full+'\n< known actual\n',expected,known)['accepted'])
        self.assertFalse(evaluation.classify(full+'\n< novel actual\n> known reference\n',expected,known)['accepted'])
        self.assertFalse(evaluation.classify(full+'\nrun-8\n< known actual\n> known reference\n',expected,known)['accepted'])
        self.assertFalse(evaluation.classify(full+'\nSegmentation fault\n',expected,known)['accepted'])
