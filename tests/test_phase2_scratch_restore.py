"""Reject silent changes to retained compiler-cache bytes and link topology."""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / 'scripts/build/phase2/verify_settings_scratch_restore.py'
SPEC = importlib.util.spec_from_file_location('scratch_restore', PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScratchRestoreTest(unittest.TestCase):
    def fixture(self, root):
        (root/'a').write_bytes(b'compiler cache')
        os.link(root/'a', root/'b')
        (root/'alias').symlink_to('a')
        rows = []
        for p in sorted(root.iterdir()):
            s = p.lstat()
            row = {'path':p.name, 'mode':s.st_mode,'uid':s.st_uid,'gid':s.st_gid,'mtime_ns':s.st_mtime_ns}
            if p.is_symlink():
                row.update(type='symlink', target='a')
            else:
                row.update(type='file', bytes=s.st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest(),hardlink_identity=[s.st_dev,s.st_ino])
            rows.append(row)
        return {'inventory':rows}

    def test_exact_fixture(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            receipt = self.fixture(root)
            self.assertTrue(MODULE.verify(root,receipt)['exact_bytes_modes_owners_timestamps_symlinks_hardlinks'])

    def test_broken_hardlink_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            receipt = self.fixture(root)
            (root/'b').unlink()
            (root/'b').write_bytes((root/'a').read_bytes())
            with self.assertRaises(AssertionError):
                MODULE.verify(root,receipt,restore_times=True)

    def test_changed_bytes_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            receipt = self.fixture(root)
            (root/'a').write_bytes(b'compiler error')
            with self.assertRaises(AssertionError):
                MODULE.verify(root,receipt,restore_times=True)
