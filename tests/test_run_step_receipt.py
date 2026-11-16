"""Independent postconditions must observe the completed recipe in durable state."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts/build'))
spec = importlib.util.spec_from_file_location('runner_receipt_test', ROOT/'scripts/build/run_step.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ReceiptTests(unittest.TestCase):
    def test_postcheck_reads_recipe_exit_and_success_requires_both(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            recipe = ROOT/'scripts/build/probe-success.sh'
            checker = ROOT/'scripts/build/probe-postcheck.sh'
            seen = []
            def execute(command, **options):
                if command[-1] == str(checker):
                    row = json.loads((state/'receipt-test.running.json').read_text())
                    self.assertEqual(row['recipe_exit'], 0)
                    self.assertIsNone(row['postcheck_exit'])
                    self.assertEqual(row['recipe_pid'], 321)
                    seen.append('actual-checker-boundary')
                return types.SimpleNamespace(returncode=0)
            process = types.SimpleNamespace(pid=321, wait=lambda: 0)
            with patch.object(runner, 'STATE', state), patch.object(runner.os, 'geteuid', return_value=0), \
                 patch.object(runner, 'snapshot', return_value={}), patch.object(runner, 'recipe_set', return_value={}), \
                 patch.object(runner.subprocess, 'run', side_effect=execute), \
                 patch.object(runner.subprocess, 'Popen', return_value=process), \
                 patch.object(sys, 'argv', ['run_step.py', 'receipt-test', str(recipe), str(checker), '--user', 'root']), \
                 patch('builtins.print'):
                runner.main()
            self.assertEqual(seen, ['actual-checker-boundary'])
            row = json.loads((state/'receipt-test.success.json').read_text())
            self.assertEqual((row['recipe_exit'], row['postcheck_exit']), (0, 0))
            self.assertFalse((state/'receipt-test.running.json').exists())

    def test_partial_atomic_state_is_preserved_for_inspection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'step.running.json'
            partial = path.with_suffix('.tmp')
            partial.write_text('interrupted write')
            with self.assertRaises(FileExistsError):
                runner.write(path, {'state': 'replacement'})
            self.assertEqual(partial.read_text(), 'interrupted write')
            self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
