"""Reject ambiguous browser storage before a QEMU attachment can occur."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/host'))
import phase2_vm


class BrowserScratchGuard(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.work = Path(directory.name)
        for name, value in [('WORK', self.work), ('FIREFOX_SCRATCH_BYTES', 8192)]:
            guard = patch.object(phase2_vm, name, value)
            guard.start()
            self.addCleanup(guard.stop)

    def prepare(self):
        disk = self.work / 'firefox-scratch.raw'
        with disk.open('wb') as stream:
            stream.write(bytes(8192))
            stream.flush()
            os.fsync(stream.fileno())
        disk.chmod(0o600)
        st = disk.stat()
        row = dict(state='prepared', filename=disk.name, format='raw', bytes=8192,
                   serial='TODDY-B02-FIREFOX', device=st.st_dev, inode=st.st_ino)
        self.write(row)
        return disk, row

    def write(self, row):
        receipt = self.work / 'firefox-scratch.json'
        receipt.write_text(json.dumps(row))
        receipt.chmod(0o600)

    def test_absent_is_optional(self):
        self.assertEqual(phase2_vm.firefox_scratch_arguments(), [])

    def test_exact_preallocated_identity(self):
        self.prepare()
        args = phase2_vm.firefox_scratch_arguments()
        self.assertIn('file=/vm/phase2/firefox-scratch.raw', args[1])
        self.assertIn('discard=ignore', args[1])
        self.assertIn('serial=TODDY-B02-FIREFOX', args[-1])

    def test_pending_even_with_valid_receipt(self):
        self.prepare()
        (self.work / 'firefox-scratch.pending.json').write_text('{}')
        with self.assertRaises(ValueError):
            phase2_vm.firefox_scratch_arguments()

    def test_partial_and_dangling_symlink(self):
        disk = self.work / 'firefox-scratch.raw'
        disk.touch()
        with self.assertRaises(ValueError):
            phase2_vm.firefox_scratch_arguments()
        disk.unlink()
        disk.symlink_to(self.work / 'missing')
        with self.assertRaises(ValueError):
            phase2_vm.firefox_scratch_arguments()

    def test_foreign_identity_or_scope(self):
        disk, row = self.prepare()
        for key, value in [('inode', row['inode'] + 1), ('device', -1),
                           ('filename', '/dev/sda'), ('state', 'preparing'),
                           ('serial', 'TODDY-LFS-TARGET'), ('bytes', 16384)]:
            with self.subTest(key=key):
                self.write(dict(row, **{key: value}))
                with self.assertRaises(ValueError):
                    phase2_vm.firefox_scratch_arguments()

    def test_sparse_file_denied(self):
        disk, row = self.prepare()
        with disk.open('wb') as stream:
            stream.truncate(8192)
        self.assertEqual(disk.stat().st_blocks, 0)
        with self.assertRaises(ValueError):
            phase2_vm.firefox_scratch_arguments()

    def test_shared_or_world_readable_files_denied(self):
        disk, row = self.prepare()
        os.link(disk, self.work / 'alias')
        with self.assertRaises(ValueError):
            phase2_vm.firefox_scratch_arguments()
        (self.work / 'alias').unlink()
        disk.chmod(0o644)
        with self.assertRaises(ValueError):
            phase2_vm.firefox_scratch_arguments()
        disk.chmod(0o600)
        (self.work / 'firefox-scratch.json').chmod(0o644)
        with self.assertRaises(ValueError):
            phase2_vm.firefox_scratch_arguments()

    def test_foreign_owner_denied(self):
        self.prepare()
        with patch.object(phase2_vm.os, 'getuid', return_value=os.getuid() + 1):
            with self.assertRaises(ValueError):
                phase2_vm.firefox_scratch_arguments()
