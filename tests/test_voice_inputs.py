import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('voice_inputs', ROOT / 'scripts/build/phase2/voice_inputs.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class Response(io.BytesIO):
    def geturl(self):
        return 'https://upstream.invalid/fixed'


class InputsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.payload = b'fixed input bytes'
        self.row = {'filename': 'input.bin', 'url': 'https://upstream.invalid/fixed',
                    'size': len(self.payload), 'sha256': hashlib.sha256(self.payload).hexdigest()}
    def tearDown(self):
        self.tmp.cleanup()
    def opener(self, *args, **kwargs):
        return Response(self.payload)

    def test_exact_acquisition_reuses_verified_input_without_network(self):
        self.assertTrue(v.fetch(self.row, self.root, opener=self.opener, reserve=0))
        self.assertEqual((self.root / 'input.bin').stat().st_mode & 0o777, 0o600)
        def unavailable(*args, **kwargs):
            raise AssertionError('verified cache should not acquire again')
        self.assertFalse(v.fetch(self.row, self.root, opener=unavailable, reserve=0))

    def test_tampering_never_replaces_input_or_invokes_network(self):
        path = self.root / 'input.bin'
        path.write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            v.fetch(self.row, self.root, opener=self.opener, reserve=0)
        self.assertEqual(path.read_bytes(), b'wrong')

    def test_short_and_oversized_download_remain_partial_never_published(self):
        for body in (b'short', self.payload + b'excess'):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                with self.assertRaises(ValueError):
                    v.fetch(self.row, directory, opener=lambda *a, **k: Response(body), reserve=0)
                self.assertFalse((directory / 'input.bin').exists())
                self.assertTrue((directory / 'input.bin.partial').exists())
                with self.assertRaises(FileExistsError):
                    v.fetch(self.row, directory, opener=self.opener, reserve=0)

    def test_reserve_refusal_occurs_before_network_or_partial_creation(self):
        with patch.object(v.shutil, 'disk_usage') as usage:
            usage.return_value.free = v.RESERVE
            with self.assertRaisesRegex(ValueError, 'reserve'):
                v.fetch(self.row, self.root, opener=self.opener)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_symlink_input_and_path_escape_are_rejected(self):
        target = self.root / 'target'
        target.write_bytes(self.payload)
        (self.root / 'input.bin').symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'integrity'):
            v.fetch(self.row, self.root, opener=self.opener, reserve=0)
        row = dict(self.row, filename='../elsewhere')
        with self.assertRaisesRegex(ValueError, 'record'):
            v.fetch(row, self.root, opener=self.opener, reserve=0)

    def test_archive_traversal_devices_and_links_fail_closed(self):
        for path, kind, link in [('root/../../escape', tarfile.REGTYPE, ''),
                                 ('root/device', tarfile.CHRTYPE, ''),
                                 ('root/link', tarfile.SYMTYPE, '/etc/shadow'),
                                 ('root/link', tarfile.LNKTYPE, 'root/file')]:
            member = tarfile.TarInfo(path);member.type = kind;member.linkname = link
            with self.subTest(path=path, kind=kind), self.assertRaises(ValueError):
                v.validate_members('espeak-source', [member])
        allowed = tarfile.TarInfo('root/src/include/espeak/speak_lib.h')
        allowed.type = tarfile.SYMTYPE;allowed.linkname = '../espeak-ng/speak_lib.h'
        self.assertEqual(v.validate_members('espeak-source', [allowed]), ('root', 0))
        with self.assertRaises(ValueError):
            v.validate_members('whisper-source', [allowed])

    def test_source_corrections_refuse_unknown_bytes(self):
        (self.root / 'CMakeLists.txt').write_text('project(unreviewed)')
        with self.assertRaisesRegex(ValueError, 'patch_input'):
            v.patch_source('whisper-source', self.root)

    def test_frozen_candidate_versions_and_exact_multilingual_model(self):
        lock = v.load_lock()
        model = next(r for r in lock['artifacts'] if r['id'] == 'whisper-base-model')
        self.assertEqual(model['filename'], 'ggml-base.bin')
        self.assertEqual(model['size'], 147951465)
        self.assertNotIn('/main/', model['url'])
        self.assertEqual(lock['reserve_bytes'], 107911053312)
        self.assertFalse(any('piper' in r['id'] for r in lock['artifacts']))


if __name__ == '__main__':
    unittest.main()
