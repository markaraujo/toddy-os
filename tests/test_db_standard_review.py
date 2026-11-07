import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/build'))
from db_standard_review import validate_failure_record


class FailedSummaryReview(unittest.TestCase):
    def test_review_does_not_relabel_process_failure_or_accept_ignored_assertions(self):
        record = {'driver_exit': 1, 'test_exit': 1,
                  'error': 'Complete native suite failed with exit 1',
                  'test_inputs_unchanged': True, 'package_accepted': False}
        validate_failure_record(record)
        self.assertEqual((record['driver_exit'], record['test_exit']), (1, 1))
        for key, value in [('driver_exit', 0), ('test_exit', 0), ('test_exit', True),
                           ('test_exit', -9), ('error', 'a different runtime failure'),
                           ('test_inputs_unchanged', False), ('package_accepted', True),
                           ('standard_suite_passed', True), ('source_protected_from_test_user', True)]:
            changed = copy.deepcopy(record)
            changed[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_failure_record(changed)
