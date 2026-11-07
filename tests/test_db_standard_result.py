import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'db_standard_result', Path(__file__).resolve().parents[1] /
    'scripts/build/db_standard_result.py')
result = importlib.util.module_from_spec(spec)
spec.loader.exec_module(result)


class DatabaseStandardResult(unittest.TestCase):
    def test_truncated_failed_duplicate_or_unexpected_summaries_are_rejected(self):
        body = 'Recorded upstream test output\nRegression Tests Succeeded\n'
        closing = 'Test suite run completed at: 01:00 11/07/2026\n'
        stdout = 'Regression Tests Succeeded\n' + result.SENTINEL + '\n'
        result.validate_summary(body + closing, stdout)
        cases = [
            (body, stdout),
            (body + closing, 'Regression Tests Succeeded\n'),
            ('FAIL: a real assertion\n' + body + closing, stdout),
            (body + body + closing, stdout),
            (body.replace('Succeeded', 'Failed') + closing, stdout),
            (body + closing, 'UNEXPECTED OUTPUT: diagnostic\n' + stdout),
            (body + closing, stdout + 'unexplained trailing output\n'),
        ]
        for report, output in cases:
            with self.subTest(report=report, output=output), self.assertRaises(ValueError):
                result.validate_summary(report, output)

    def records(self):
        base = Path('/mnt/lfs/sources/recovery/db-standard-unit')
        inputs = {'fixture': str(base), 'native_build_seed_sha256': result.SEED_SHA256,
                  'verified_seed_files': 460, 'verified_tcl_files': 483,
                  'isolation_script_sha256': result.ISOLATION_SHA256,
                  'isolation_probe_sha256': result.PROBE_SHA256,
                  'source_files': {str(i): {} for i in range(943)}}
        record = {'fixture': str(base), 'driver_exit': 0, 'test_exit': 0,
                  'standard_suite_passed': True, 'source_protected_from_test_user': True,
                  'test_inputs_unchanged': True, 'package_accepted': False,
                  'driver_sha256': result.DRIVER_SHA256,
                  'command': ['timeout', '--kill-after=60', '172800', 'bash',
                              str(base / 'isolate.sh'), str(base), 'standard'],
                  'reports': {name: result.CUTEST_SHA256 for name in result.REPORTS},
                  'verified_input_files': 943, 'started': '2026-11-07T00:00:00+00:00',
                  'finished': '2026-11-07T01:00:00+00:00'}
        return base, inputs, record

    def test_exit_codes_flags_and_profile_cannot_be_replaced_by_success_claim(self):
        base, inputs, record = self.records()
        result.validate_record(record, inputs, base)
        changes = [('driver_exit', 1), ('test_exit', -9), ('test_exit', False),
                   ('standard_suite_passed', False), ('test_inputs_unchanged', False),
                   ('source_protected_from_test_user', False), ('package_accepted', True),
                   ('driver_sha256', '0' * 64), ('error', 'ignored failure'),
                   ('command', ['tclsh', 'one-focused-case.tcl']), ('reports', {}),
                   ('fixture', str(base) + '-different'), ('verified_input_files', 1)]
        for key, value in changes:
            changed = copy.deepcopy(record)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                result.validate_record(changed, inputs, base)
        altered = copy.deepcopy(inputs)
        altered['verified_tcl_files'] = 482
        with self.assertRaises(ValueError):
            result.validate_record(record, altered, base)
        altered = copy.deepcopy(inputs)
        altered['isolation_probe_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            result.validate_record(record, altered, base)
