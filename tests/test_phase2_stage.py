"""Staged compiler output cannot supply escaping links, devices or stale receipts."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verify_stage', ROOT / 'scripts/build/phase2/verify_stage.py')
stage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)


class StageValidation(unittest.TestCase):
    def test_internal_relative_library_link_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'library.so.1').write_bytes(b'fixture')
            (root / 'library.so').symlink_to('library.so.1')
            result = stage.inspect_stage(root)
            self.assertEqual(result['entries']['library.so']['symlink'], 'library.so.1')

    def test_escaping_and_absolute_links_are_rejected(self):
        for target in ['../outside', '/etc/passwd']:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'escape').symlink_to(target)
                with self.assertRaisesRegex(ValueError, 'escaping staged link'):
                    stage.inspect_stage(root)

    def test_devices_and_privileged_payloads_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            os.mkfifo(root / 'fifo')
            with self.assertRaisesRegex(ValueError, 'Special staged file'):
                stage.inspect_stage(root)
            (root / 'fifo').unlink()
            (root / 'setuid').write_bytes(b'fixture')
            (root / 'setuid').chmod(0o4755)
            with self.assertRaisesRegex(ValueError, 'Privileged'):
                stage.inspect_stage(root)

    def test_modified_or_removed_output_invalidates_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'one').write_bytes(b'original')
            (root / 'two').write_bytes(b'keep')
            original = stage.inspect_stage(root)['manifest_sha256']
            (root / 'one').write_bytes(b'changed')
            modified = stage.inspect_stage(root)['manifest_sha256']
            self.assertNotEqual(original, modified)
            (root / 'one').unlink()
            self.assertNotEqual(modified, stage.inspect_stage(root)['manifest_sha256'])
