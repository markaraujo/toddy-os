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


if __name__ == '__main__':
    unittest.main()
