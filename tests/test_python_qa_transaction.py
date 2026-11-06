import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/build'))
from python_qa_transaction import atomic_json, execute, verify_payload


class PythonQATransaction(unittest.TestCase):
    def test_redirected_journal_is_rejected_before_package_operations(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / 'original.json'
            original.write_text('{}')
            journal = root / 'transaction.json'
            journal.symlink_to(original.name)
            with self.assertRaisesRegex(ValueError, 'explicit native guest target'):
                execute(SimpleNamespace(native=True, target=root), root, [], [], journal, donor_record_sha256='')
            self.assertEqual(original.read_text(), '{}')

    def test_modified_or_ambiguously_owned_runtime_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            file = root / 'usr/lib/python3.14/ssl.py'
            file.parent.mkdir(parents=True)
            file.write_bytes(b'preserved runtime\n')
            stat = file.stat()
            virtual = '/' + str(file.relative_to(root))
            record = {'name': 'python', 'payload': {virtual: {'mode': stat.st_mode,
                      'uid': stat.st_uid, 'gid': stat.st_gid, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}}}
            owners = {virtual: {'python'}}
            self.assertEqual(verify_payload(root, record, owners), 1)
            with self.assertRaisesRegex(ValueError, 'ownership'):
                verify_payload(root, record, {virtual: {'python', 'other'}})
            file.write_bytes(b'changed runtime\n')
            with self.assertRaisesRegex(ValueError, 'bytes differ'):
                verify_payload(root, record, owners)

    def test_payload_parent_redirect_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / 'outside'
            outside.mkdir()
            (outside / 'file').write_bytes(b'original')
            (root / 'redirect').symlink_to('outside')
            info = (outside / 'file').stat()
            record = {'name': 'python', 'payload': {'/redirect/file': {
                'mode': info.st_mode, 'uid': info.st_uid, 'gid': info.st_gid,
                'sha256': hashlib.sha256(b'original').hexdigest()}}}
            with self.assertRaisesRegex(ValueError, 'parent redirects'):
                verify_payload(root, record, {'/redirect/file': {'python'}})

    def test_durable_journal_replacement_preserves_target_of_redirect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            journal = root / 'transaction.json'
            atomic_json(journal, {'actions': [], 'complete': False})
            atomic_json(journal, {'actions': [{'action': 'install_core', 'exit': None}], 'complete': False})
            self.assertIsNone(json.loads(journal.read_text())['actions'][0]['exit'])
            self.assertEqual(journal.stat().st_mode & 0o777, 0o600)
            original = journal.read_bytes()
            redirect = root / 'redirect.json'
            redirect.symlink_to(journal.name)
            with self.assertRaisesRegex(ValueError, 'redirects'):
                atomic_json(redirect, {'complete': True})
            self.assertEqual(journal.read_bytes(), original)
            self.assertEqual({path.name for path in root.iterdir()}, {'transaction.json', 'redirect.json'})


if __name__ == '__main__':
    unittest.main()
