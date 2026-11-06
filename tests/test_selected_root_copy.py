import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('copy_selected_root', Path(__file__).resolve().parents[1] / 'scripts/build/h10/copy_selected_root.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SelectedRootCopy(unittest.TestCase):
    def test_inventory_requires_canonical_paths_and_explicit_parents(self):
        for names in ([], ['usr'], ['.', '.'], ['.', '../outside'], ['.', '/etc'],
                      ['.', 'usr/bin/file'], ['.', 'usr//bin'], ['.', None], ['.', 'a\0b']):
            with self.subTest(names=names), self.assertRaises(ValueError):
                module.checked_names(names)
        self.assertEqual(set(module.checked_names(['.', '--literal-option', 'space λ\nline'])),
                         {'.', '--literal-option', 'space λ\nline'})

    def test_snapshot_keeps_hardlink_identity_and_excludes_unselected_siblings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'one').write_bytes(b'selected bytes')
            os.link(root / 'one', root / 'two')
            (root / 'omitted').write_bytes(b'not selected')
            (root / 'alias').symlink_to('one')
            result = module.snapshot(root, ['.', 'one', 'two', 'alias'])
            self.assertEqual(set(result['entries']), {'.', 'one', 'two', 'alias'})
            self.assertEqual(result['hardlink_groups'], [['one', 'two']])
            self.assertEqual(result['entries']['alias']['symlink'], 'one')
            (root / 'two').unlink()
            (root / 'two').write_bytes(b'selected bytes')
            self.assertEqual(module.snapshot(root, ['.', 'one', 'two', 'alias'])['hardlink_groups'], [])

    def test_redirected_parent_and_special_node_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'real').mkdir()
            (root / 'real/file').write_bytes(b'private harmless fixture')
            (root / 'redirect').symlink_to('real')
            with self.assertRaisesRegex(ValueError, 'parent redirects'):
                module.snapshot(root, ['.', 'redirect', 'redirect/file'])
            os.mkfifo(root / 'pipe')
            with self.assertRaisesRegex(ValueError, 'special node'):
                module.snapshot(root, ['.', 'pipe'])


if __name__ == '__main__':
    unittest.main()
