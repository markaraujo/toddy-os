"""Real-file interruption, reconstruction and corruption guards for cold custody."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts/host'
sys.path.insert(0, str(SCRIPTS))
import phase2_chunk_cold_checkpoint as custody


class ChunkCustodyTest(unittest.TestCase):
    def fixture(self, directory):
        data = b'a' * 4096 + os.urandom(4096) + b'\0' * 123
        source = directory / 'source.custody'
        source.write_bytes(data)
        state = {'state': 'compressing', 'bytes': len(data),
                 'source_sha256': hashlib.sha256(data).hexdigest(), 'chunks': []}
        return data, source, state

    def test_interruption_resume_retains_exact_bytes(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(custody, 'CHUNK', 4096):
            directory = Path(temporary)
            data, source, state = self.fixture(directory)
            with source.open('r+b') as f:
                with self.assertRaises(InterruptedError):
                    custody.process(directory, state, f.fileno(), reserve=0, fail_after_verify=True)
                self.assertEqual(source.read_bytes(), data)
                state = json.loads((directory / 'result.json').read_text())
                # Simulate interruption after the durable punch but before its receipt.
                custody.punch(f.fileno(), 0, 4096)
                custody.process(directory, state, f.fileno(), reserve=0)
                self.assertEqual(state['state'], 'complete')
                restored = b''.join(custody.chunk_data(directory, r) for r in state['chunks'])
                self.assertEqual(restored, data)
                self.assertFalse(any(source.read_bytes()))

    def test_corrupt_archive_refuses_source_retirement(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(custody, 'CHUNK', 4096):
            directory = Path(temporary)
            data, source, state = self.fixture(directory)
            with source.open('r+b') as f:
                with self.assertRaises(InterruptedError):
                    custody.process(directory, state, f.fileno(), reserve=0, fail_after_verify=True)
                (directory / state['chunks'][0]['archive']).write_bytes(b'corruption')
                with self.assertRaises(AssertionError):
                    custody.process(directory, state, f.fileno(), reserve=0)
                self.assertEqual(source.read_bytes(), data)

    def test_changed_unarchived_source_refused(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(custody, 'CHUNK', 4096):
            directory = Path(temporary)
            data, source, state = self.fixture(directory)
            with source.open('r+b') as f:
                f.write(b'!')
                f.flush()
                with self.assertRaises(AssertionError):
                    custody.process(directory, state, f.fileno(), reserve=0)
                self.assertEqual(state['chunks'], [])


if __name__ == '__main__':
    unittest.main()
