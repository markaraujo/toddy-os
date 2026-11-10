"""Prevent a remote diagnostic or failed local unit becoming false acceptance."""
import ast
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CupsResultSelectionTests(unittest.TestCase):
    def setUp(self):
        recipe = (ROOT / 'scripts/build/phase2/cups-build.sh').read_text()
        collector = recipe.split("python3 - <<'PY'\n")[-1].rsplit('\nPY', 1)[0]
        function = next(n for n in ast.parse(collector).body if isinstance(n, ast.FunctionDef) and n.name == 'select_local_results')
        namespace = {}
        exec(compile(ast.Module(body=[function], type_ignores=[]), '<CUPS-result-selection>', 'exec'), namespace)
        self.select = namespace['select_local_results']
        evidence = json.loads((ROOT / 'docs/evidence/B02-cups-local-tests-checkpoint.json').read_text())
        self.raw = evidence['original_results']
        self.log = evidence['SNMP_log']

    def test_actual_raw_rows_remain_unchanged_and_snmp_unqualified(self):
        before = copy.deepcopy(self.raw)
        selected, diagnostic = self.select(self.raw, self.log)
        self.assertEqual(self.raw, before)
        self.assertEqual(len(selected), 9)
        self.assertFalse(diagnostic['qualified'])
        self.assertEqual(diagnostic['exit'], 1)

    def test_failed_local_unit_cannot_be_excluded(self):
        self.raw[4]['exit'] = 1
        with self.assertRaises(AssertionError):
            self.select(self.raw, self.log)

    def test_different_diagnostic_outcome_cannot_be_reclassified(self):
        self.raw[-1]['exit'] = 0
        with self.assertRaises(AssertionError):
            self.select(self.raw, self.log)

    def test_missing_or_duplicate_local_program_is_refused(self):
        self.raw[4]['name'] = 'testipp'
        with self.assertRaises(AssertionError):
            self.select(self.raw, self.log)
