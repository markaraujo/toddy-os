import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts/build/h10/initramfs_runtime.py'
spec = importlib.util.spec_from_file_location('toddy_initramfs_runtime', MODULE)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class InitramfsRuntimeSafety(unittest.TestCase):
    def test_credentials_and_noncanonical_paths_cannot_be_payload(self):
        for path in ('/etc/shadow', '/root/.ssh/id_ed25519', '/proc/self/mem',
                     '/usr/lib/../../etc/passwd', '//usr/lib/libc.so.6',
                     '/usr/lib/./libc.so.6', 'usr/bin/bash', '/usr/bin/bad\nname'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                runtime.destination_path(path)
        self.assertEqual(runtime.destination_path('/lib64/ld-linux-x86-64.so.2'),
                         'usr/lib/ld-linux-x86-64.so.2')

    def test_stage_rejects_existing_or_redirected_destination_before_query(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'tmp').mkdir()
            existing = root / 'tmp/existing'
            existing.mkdir()
            (existing / 'preserve').write_text('do not replace')
            redirected = root / 'tmp/redirected'
            redirected.symlink_to(existing, target_is_directory=True)
            for stage in (existing, redirected / 'new'):
                with self.assertRaisesRegex(ValueError, 'existing/redirected'):
                    runtime.stage_runtime(root, stage, root / 'absent-records')
            self.assertEqual((existing / 'preserve').read_text(), 'do not replace')
            self.assertFalse((existing / 'new').exists())

    def test_stage_rejects_live_configuration_directory_before_query(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'etc').mkdir()
            with self.assertRaisesRegex(ValueError, 'staging or private temporary'):
                runtime.stage_runtime(root, root / 'etc/runtime', root / 'absent-records')
            self.assertFalse((root / 'etc/runtime').exists())


if __name__ == '__main__':
    unittest.main()
