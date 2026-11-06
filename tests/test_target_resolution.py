"""Absolute target symlinks must resolve under the target, never builder /usr."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('native_elf_audit', Path(__file__).resolve().parents[1] / 'scripts/build/audit_native_elf.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class TargetResolution(unittest.TestCase):
    def test_absolute_and_usrmerge_links_stay_inside_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'usr/lib').mkdir(parents=True)
            (root / 'lib').symlink_to('usr/lib')
            (root / 'usr/lib/alias.so').symlink_to('/lib/real.so')
            (root / 'usr/lib/real.so').write_bytes(b'target library')
            path, virtual = audit.target_resolve(root, '/lib/alias.so')
            self.assertEqual(path, root / 'usr/lib/real.so')
            self.assertEqual(virtual, '/usr/lib/real.so')
            self.assertEqual(path.read_bytes(), b'target library')

    def test_parent_components_cannot_escape_and_loops_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(audit.target_resolve(root, '/../../usr/lib')[0], root / 'usr/lib')
            (root / 'loop').symlink_to('/loop')
            with self.assertRaises(ValueError):
                audit.target_resolve(root, '/loop')
