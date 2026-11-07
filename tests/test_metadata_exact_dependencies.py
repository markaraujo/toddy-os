"""Preserve ABI pins while ordering/retargeting metadata-only revisions."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/build'))
from upgrade_native_metadata import retarget_exact_dependencies,exact_dependency_order

class ExactMetadataTests(unittest.TestCase):
    def test_exact_pin_follows_same_frozen_provider(self):
        self.assertEqual(retarget_exact_dependencies('glibc (= 2.44-1), bash (>= 5.3-1)',
            {'glibc':('2.44-1+toddy1','amd64','')}),'glibc (= 2.44-1+toddy1), bash (>= 5.3-1)')
    def test_source_version_change_is_not_a_metadata_upgrade(self):
        with self.assertRaisesRegex(ValueError,'frozen source'):
            retarget_exact_dependencies('glibc (= 2.44-1)',{'glibc':('2.45-1+toddy1','amd64','')})
    def test_provider_precedes_alphabetically_earlier_consumer(self):
        packages={'gcc':('16.2.0-1','amd64','gcc-runtime (= 16.2.0-1)'),
                  'gcc-runtime':('16.2.0-1','amd64','glibc (>= 2.44-1)')}
        self.assertEqual(exact_dependency_order(packages),['gcc-runtime','gcc'])
    def test_cycle_and_missing_provider_fail_before_mutation(self):
        with self.assertRaisesRegex(ValueError,'Cyclic'):
            exact_dependency_order({'a':('1','all','b (= 1)'),'b':('1','all','a (= 1)')})
        with self.assertRaisesRegex(ValueError,'Missing'):
            exact_dependency_order({'a':('1','all','b (= 1)')})

if __name__=='__main__':unittest.main()
