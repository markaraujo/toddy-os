import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts/build/h10/initramfs_archive.py'
spec = importlib.util.spec_from_file_location('toddy_initramfs_archive', MODULE)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


def newc(name, body=b'', mode=0o100644):
    name = name.encode() + b'\0'
    fields = [1, mode, 0, 0, 1, 0, len(body), 0, 0, 0, 0, len(name), 0]
    raw = b'070701' + ''.join(f'{v:08x}' for v in fields).encode() + name
    raw += b'\0' * (-len(raw) % 4)
    raw += body
    return raw + b'\0' * (-len(raw) % 4)


class InitramfsArchive(unittest.TestCase):
    def test_exact_payload_and_metadata_are_required(self):
        expected = {'init': {'mode': 0o100755, 'size': 4, 'rdev': [0, 0],
                            'body_sha256': hashlib.sha256(b'init').hexdigest()}}
        trailer = newc('TRAILER!!!')
        valid = newc('init', b'init', 0o100755) + trailer
        self.assertEqual(archive.validate_newc(valid, expected, 0), 1)
        for changed in (newc('init', b'evil', 0o100755) + trailer,
                        newc('init', b'init', 0o100644) + trailer,
                        newc('init', b'init', 0o100755) * 2 + trailer,
                        valid + b'unexpected', valid[:100], trailer):
            with self.subTest(changed=changed[:20]), self.assertRaises(ValueError):
                archive.validate_newc(changed, expected, 0)

    def test_unsafe_name_is_rejected_even_if_expected(self):
        for name in ('/init', '../escape', 'usr/../../escape', 'usr/./init'):
            expected = {name: {'mode': 0o100644, 'size': 0, 'rdev': [0, 0],
                               'body_sha256': hashlib.sha256(b'').hexdigest()}}
            with self.subTest(name=name), self.assertRaises(ValueError):
                archive.validate_newc(newc(name) + newc('TRAILER!!!'), expected, 0)

    def test_existing_or_redirected_work_is_preserved_before_native_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'tmp').mkdir()
            existing = root / 'tmp/existing'
            existing.mkdir()
            marker = existing / 'keep'
            marker.write_text('retained')
            alias = root / 'tmp/alias'
            alias.symlink_to(existing, target_is_directory=True)
            for work in (existing, alias / 'new', root / 'etc/new'):
                with self.subTest(work=work), self.assertRaisesRegex(ValueError, 'private target storage'):
                    archive.assemble(root, work, root / 'absent', root / 'absent', root / 'absent',
                                     '0' * 64, '1' * 64, 0)
            self.assertEqual(marker.read_text(), 'retained')
            self.assertFalse((existing / 'new').exists())


if __name__ == '__main__':
    unittest.main()
