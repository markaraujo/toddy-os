"""Source corruption must fail before extraction or successful locking."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fetch_sources', ROOT / 'scripts/fetch_sources.py')
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


class SourceIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cache = Path(self.temp.name)
        self.contents = b'example upstream archive bytes'
        self.row = {'filename': 'example-1.tar.xz', 'url': 'https://example.org/example-1.tar.xz',
                    'upstream_md5': hashlib.md5(self.contents).hexdigest(), 'sha256': None}
        (self.cache / self.row['filename']).write_bytes(self.contents)
        self.patcher = patch.object(fetcher, 'CACHE', self.cache)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_corrupt_cache_is_rejected_without_network(self):
        (self.cache / self.row['filename']).write_bytes(b'corrupt')
        with patch.object(fetcher.subprocess, 'run') as network:
            with self.assertRaisesRegex(ValueError, 'upstream integrity mismatch'):
                fetcher.fetch(self.row)
            network.assert_not_called()

    def test_sha256_pin_is_enforced_even_when_md5_matches(self):
        self.row['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Frozen SHA-256 mismatch'):
            fetcher.fetch(self.row)

    def test_source_filename_cannot_escape_cache(self):
        self.row['filename'] = '../outside'
        with self.assertRaisesRegex(ValueError, 'Unsafe filename'):
            fetcher.fetch(self.row)


if __name__ == '__main__':
    unittest.main()
