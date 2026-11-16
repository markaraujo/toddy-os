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

    def test_installer_profile_preserves_prior_selections_and_stricter_reserve(self):
        self.assertEqual(custody.PROFILES['installer-capacity'],
            ('h07-native-services-target.qcow2', 'cold-installer-chunk-custody-1',
             (11832773, 61737336832, 1793953144185127409)))
        expected = {
            'math': ('h07-native-math-builder.qcow2', 'cold-math-chunk-custody-1',
                     (11832185, 5940445184, 1793935345557250551)),
            'firefox-capacity': ('h07-gcc-tested-target.qcow2', 'cold-firefox-chunk-custody-1',
                                (11832380, 34298068992, 1793940369084300644)),
            'native-capacity': ('h07-gcc-tested-builder.qcow2', 'cold-native-chunk-custody-1',
                               (11832378, 5949423616, 1793940344780548431))}
        self.assertEqual({key: custody.PROFILES[key] for key in expected}, expected)
        self.assertEqual(custody.PROFILE_RESERVES, {'installer-capacity': 100 * 1024**3 + 512 * 1024**2})

    def test_completed_chunks_restore_exact_absent_file_and_metadata_retaining_archives(self):
        # Qualification of the documented restore sequence on temporary bytes only.
        with tempfile.TemporaryDirectory() as temporary, patch.object(custody, 'CHUNK', 4096):
            directory = Path(temporary)
            data, source, state = self.fixture(directory)
            source.chmod(0o640)
            os.utime(source, ns=(1700000000000000000, 1700000000000000123))
            metadata = source.stat()
            with source.open('r+b') as stream:
                custody.process(directory, state, stream.fileno(), reserve=0)
            archives = {row['archive']: (directory / row['archive']).read_bytes() for row in state['chunks']}
            output, part = directory / 'restored.qcow2', directory / 'restored.part'
            descriptor = os.open(part, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            self.assertEqual(part.stat().st_mode & 0o7777, 0o600)
            with os.fdopen(descriptor, 'wb') as stream:
                for row in sorted(state['chunks'], key=lambda row: row['offset']):
                    self.assertEqual(stream.tell(), row['offset'])
                    stream.write(custody.chunk_data(directory, row))
                stream.flush(); os.fsync(stream.fileno())
            self.assertEqual(part.stat().st_size, state['bytes'])
            self.assertEqual(custody.cold.sha(part), state['source_sha256'])
            part.chmod(metadata.st_mode & 0o7777)
            os.utime(part, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
            with part.open('rb') as stream:
                os.fsync(stream.fileno())
            self.assertFalse(output.exists())
            os.link(part, output); custody.syncdir(directory)
            part.unlink(); custody.syncdir(directory)
            self.assertEqual(output.stat().st_mtime_ns, metadata.st_mtime_ns)
            self.assertEqual(output.stat().st_mode & 0o7777, 0o640)
            self.assertEqual(output.stat().st_uid, metadata.st_uid)
            self.assertEqual(output.read_bytes(), data)
            self.assertEqual(archives, {name: (directory / name).read_bytes() for name in archives})
            with self.assertRaises(FileExistsError):
                os.link(output, output)

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
