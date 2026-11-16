import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/host'))
spec = importlib.util.spec_from_file_location('export_transfer', ROOT / 'scripts/host/collect_package_export2.py')
transfer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transfer)


class ExportTransferTests(unittest.TestCase):
    def fixture(self):
        sha = 'a' * 64
        return {'kind': 'unsigned-flat-native-archive-export', 'signed': False,
            'published': False, 'files': {name: sha for name in transfer.FIXED} |
            {'test_' + sha + '.deb': sha}, 'packages': [
                {'asset': 'test_' + sha + '.deb', 'archive_sha256': sha, 'archive_bytes': 3}]}

    def test_select_exact_flat_receipt(self):
        value = self.fixture()
        result = transfer.selected(json.dumps(value).encode())
        self.assertEqual(set(result), set(value['files']) | {'archive-export.json'})

    def test_refuse_unrelated_or_private_paths(self):
        for name in ('../private', 'private.asc', 'directory/key.gpg', 'Release.gpg'):
            value = self.fixture()
            value['files'][name] = 'a' * 64
            with self.assertRaises(ValueError):
                transfer.selected(json.dumps(value).encode())
