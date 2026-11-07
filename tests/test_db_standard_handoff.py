import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

BUILD = Path(__file__).resolve().parents[1] / 'scripts/build'
sys.path.insert(0, str(BUILD))
spec = importlib.util.spec_from_file_location('db_standard_handoff', BUILD / 'db_standard_handoff.py')
handoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handoff)


class OriginalDatabaseFailure(unittest.TestCase):
    def test_unknown_failures_changes_and_incomplete_original_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = {name: Path(directory) / name for name in handoff.ORIGINAL}
            paths['recipe.log'].write_text('actual original recipe output\n')
            record = {'started': handoff.OLD_START, 'recipe_sha256': handoff.OLD_RECIPE,
                      'recipe_exit': 1, 'postcheck_exit': None, 'changed_paths': 0,
                      'log_sha256': handoff.digest(paths['recipe.log'])}
            paths['failed.json'].write_text(json.dumps(record))
            paths['manifest.json'].write_text('{}')
            paths['driver.exit'].write_text('1\n')
            report = '\n'.join(handoff.FAILURES + [
                'Regression Tests Failed', 'Test suite run completed at: 01:00 11/07/26']) + '\n'
            paths['ALL.OUT'].write_text(report)
            stdout = '\n'.join(['UNEXPECTED OUTPUT: ' + line for line in handoff.FAILURES] +
                               ['Complete DB regression summary failed']) + '\n'
            paths['standard.log'].write_text(stdout)
            # Unit-only small reports exercise hash binding. The real native
            # probe uses the unchanged production pins and complete 12 MB log.
            pins = patch.multiple(handoff,
                OLD_ALL_OUT_SHA256=handoff.digest(paths['ALL.OUT']),
                OLD_STANDARD_SHA256=handoff.digest(paths['standard.log']))
            pins.start()
            self.addCleanup(pins.stop)
            handoff.validate_original(paths)
            cases = [('manifest.json', '{"/usr/bin/changed": {}}'), ('driver.exit', '0'),
                     ('ALL.OUT', report + 'FAIL: new unrelated failure\n'),
                     ('ALL.OUT', report.replace('Regression Tests Failed\n', '')),
                     ('standard.log', stdout + 'unexplained output\n'),
                     ('recipe.log', 'changed log'),
                     ('failed.json', json.dumps(dict(record, postcheck_exit=0))),
                     ('failed.json', json.dumps(dict(record, recipe_exit=True))),
                     ('failed.json', json.dumps(dict(record, changed_paths=1)))]
            for name, value in cases:
                before = paths[name].read_text()
                paths[name].write_text(value)
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    handoff.validate_original(paths)
                paths[name].write_text(before)

    def test_nomination_does_not_replace_an_existing_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'candidate.json'
            handoff.write_new(path, {'package_accepted': False})
            before = path.read_bytes()
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                handoff.write_new(path, {'package_accepted': True})
            self.assertEqual(path.read_bytes(), before)
