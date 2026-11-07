import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('db_progress',
    Path(__file__).resolve().parents[1] / 'scripts/build/db_standard_progress.py')
progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)


class StandardProgressTests(unittest.TestCase):
    def test_repeated_test044_does_not_identify_outer_group(self):
        for count, group in ((18, 'partition'), (19, 'compression'), (27, 'access-method matrix')):
            with self.subTest(group=group):
                log = '\n'.join(progress.HEADERS[:count]) + '\nTest044: btree\n'
                result = progress.classify(log)
                self.assertEqual(result['group'], group)
                self.assertEqual(result['group_number'], count)
                self.assertFalse(result['time_percent_estimated'])

    def test_final_method_position_is_separate_from_group(self):
        for index, method in enumerate(progress.METHODS):
            result = progress.classify('\n'.join(progress.HEADERS[:27 + index]))
            self.assertEqual(result['group_number'], 27)
            self.assertEqual(result['access_method'], method)
            self.assertEqual(result['access_method_number'], index + 1)
            self.assertTrue(result['returned_groups_are_not_pass_claims'])

    def test_missing_duplicate_unknown_and_skipped_headers_refuse(self):
        for headers in ([], ['Test044: btree'], ['Running unknown tests'],
                        progress.HEADERS[:2] + progress.HEADERS[:1], progress.HEADERS[1:]):
            with self.subTest(headers=headers):
                with self.assertRaises(ValueError):
                    progress.classify('\n'.join(headers))

    def test_compression_reports_real_remaining_groups(self):
        result = progress.classify('\n'.join(progress.HEADERS[:19]))
        self.assertEqual(result['remaining_after_current'], progress.GROUPS[19:])
        self.assertIsNone(result['access_method'])
        self.assertEqual(result['group_count'], 27)
        self.assertEqual(result['outer_header_count'], 35)

    def test_replication_configuration_replaces_previous_access_method(self):
        for prefix in ('Repmgr', 'Rep', 'Sec'):
            header = prefix + '024 (btree): current configuration'
            step = '\t' + prefix + '024.h: current operation'
            result = progress.details(iter(['Test142: btree -compress\n', header, step]))
            self.assertEqual(result['configuration'], header)
            self.assertEqual(result['last_case'], step.strip())
            self.assertNotIn('progress', result)

    def test_automated_replication_details_keep_failures_and_bounded_tail(self):
        for kind in ('', 'election ', 'init '):
            header = 'Repmgr003: automated replication configurations'
            dispatch = 'To reproduce this case: basic_repmgr_init_test 100 1 0 1 0 0'
            step = '\tBasic repmgr ' + kind + 'test.h: current operation'
            failure = 'FAIL: synthetic parser regression'
            lines = ['older output'] * 8 + [header, dispatch, step, failure]
            result = progress.details(iter(lines))
            self.assertEqual(result['configuration'], header)
            self.assertEqual(result['last_case'], step.strip())
            self.assertEqual(result['last_dispatch'], dispatch)
            self.assertEqual(result['failures'], [failure])
            self.assertEqual(result['tail'], lines[-5:])


if __name__ == '__main__':
    unittest.main()
