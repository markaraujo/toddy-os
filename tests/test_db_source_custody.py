import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/build'))
from db_source_custody import save, snapshot


class SourceCustodyBoundaries(unittest.TestCase):
    def test_completed_receipt_is_private_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'
            save(target, {'package_accepted': False})
            original = target.read_bytes()
            inode = target.stat().st_ino
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                save(target, {'package_accepted': True})
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(target.stat().st_ino, inode)
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_external_aliases_and_special_entries_refuse_before_metadata_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / 'source'
            source.mkdir()
            data = source / 'data'
            data.write_text('retained bytes')
            before = data.stat()
            os.link(data, base / 'outside')
            with self.assertRaisesRegex(ValueError, 'hardlink outside'):
                snapshot(source)
            (base / 'outside').unlink()
            os.link(data, source / 'inside')
            self.assertEqual(len(snapshot(source)), 3)
            (source / 'alias').symlink_to(base / 'missing-outside')
            with self.assertRaisesRegex(ValueError, 'alias escapes'):
                snapshot(source)
            (source / 'alias').unlink()
            os.mkfifo(source / 'fifo')
            with self.assertRaisesRegex(ValueError, 'Special entry'):
                snapshot(source)
            self.assertEqual(data.read_text(), 'retained bytes')
            after = data.stat()
            self.assertEqual((before.st_uid, before.st_gid, before.st_mode),
                             (after.st_uid, after.st_gid, after.st_mode))
