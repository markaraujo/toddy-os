import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/host'))
from phase2_fetch_book_source import dependency_reference_allowed


class FrozenLeafDependencies(unittest.TestCase):
    def parent(self):
        return [{'name':'pytest','reference':'BLFS13.1-systemd general/python-modules.html#pytest',
                 'book_page_sha256':'frozen'}]

    def node(self, reference):
        self.assertEqual(reference, 'general/python-modules.html#pytest')
        return {'book_page_sha256':'frozen','edges':[
            {'reference':'general/python-dependencies.html#pluggy','kind':'required'},
            {'reference':'general/python-dependencies.html#setuptools_scm','kind':'recommended'},
            {'reference':'general/python-modules.html#requests','kind':'optional'}]}

    def test_only_explicit_required_or_recommended_dependency(self):
        for ref in ['general/python-dependencies.html#pluggy',
                    'general/python-dependencies.html#setuptools_scm']:
            self.assertTrue(dependency_reference_allowed(ref, 'pytest', self.parent(), self.node))
        for ref in ['general/python-modules.html#requests', 'unrelated.html']:
            self.assertFalse(dependency_reference_allowed(ref, 'pytest', self.parent(), self.node))

    def test_unknown_duplicate_or_changed_parent_rejected(self):
        for rows in [[], self.parent()*2,
                     [{'name':'pytest','reference':'BLFS13.1-systemd general/python-modules.html#pytest',
                       'book_page_sha256':'changed'}]]:
            with self.assertRaises(AssertionError):
                dependency_reference_allowed('unrelated.html', 'pytest', rows, self.node)


if __name__ == '__main__':
    unittest.main()
