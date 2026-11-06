import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('private_key_audit', Path(__file__).resolve().parents[1] / 'scripts/build/h11/audit_private_key_material.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class PrivateKeyAudit(unittest.TestCase):
    def test_chunk_boundary_and_all_supported_headers_without_content_disclosure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            labels = ('PRIVATE KEY', 'RSA PRIVATE KEY', 'EC PRIVATE KEY', 'DSA PRIVATE KEY',
                      'ENCRYPTED PRIVATE KEY', 'OPENSSH PRIVATE KEY', 'PGP PRIVATE KEY BLOCK')
            for index, label in enumerate(labels):
                (root / str(index)).write_bytes(b'X' * (audit.BLOCK_SIZE - 8)
                    + ('-----BEGIN ' + label + '-----\n').encode() + b'Harmless-placeholder-not-a-key')
            report = audit.scan(root)
            self.assertEqual(len(report['findings']), len(labels))
            serialized = json.dumps(report)
            self.assertNotIn('Harmless-placeholder', serialized)
            self.assertNotIn('-----BEGIN', serialized)

    def test_certificates_public_keys_and_external_links_are_not_private_key_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve()
            root = parent / 'root'; root.mkdir()
            (root / 'public').write_text('-----BEGIN CERTIFICATE-----\n-----BEGIN PUBLIC KEY-----\n')
            (parent / 'outside').write_text('-----BEGIN PRIVATE KEY-----\n')
            (root / 'alias').symlink_to(parent / 'outside')
            report = audit.scan(root)
            self.assertEqual(report['findings'], [])
            self.assertEqual(report['regular_files_scanned'], 1)
            self.assertEqual(report['symlinks_not_followed'], 1)

    def test_redirected_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve()
            root = parent / 'root'; root.mkdir()
            alias = parent / 'alias'; alias.symlink_to(root)
            with self.assertRaises(ValueError):
                audit.scan(alias)


if __name__ == '__main__':
    unittest.main()
