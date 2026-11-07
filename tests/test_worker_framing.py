"""Strict protocol boundaries without requiring Node, a model or network."""
import importlib.util
import os
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('worker_protocol', ROOT / 'runtime/broker/protocol.py')
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)


class WorkerFraming(unittest.TestCase):
    def pipe(self, payload):
        read, write = os.pipe()
        self.addCleanup(os.close, read)
        os.write(write, payload)
        os.close(write)
        return os.fdopen(read, 'rb', closefd=False)

    def test_unicode_frame_roundtrip(self):
        message = {'text': 'Toddy 🐶', 'sequence': 42}
        with self.pipe(protocol.encode(message)) as stream:
            self.assertEqual(protocol.read_frame(stream), message)

    def test_duplicate_invalid_utf8_and_unsafe_numbers(self):
        for value in [b'{"x":1,"x":2}', b'{"x":1,"\\u0078":2}', b'NaN', b'Infinity',
                      b'1e999', b'9007199254740992', b'"\\ud800"', b'\xff', b'{} false']:
            with self.subTest(value=value), self.assertRaises((ValueError, UnicodeError)):
                protocol.strict_json(value)

    def test_depth_bound(self):
        with self.assertRaisesRegex(ValueError, 'json_depth'):
            protocol.strict_json(b'[' * 66 + b'0' + b']' * 66)

    def test_oversized_header_rejected_before_body(self):
        with self.pipe(struct.pack('>I', protocol.MAX_FRAME + 1)) as stream:
            with self.assertRaisesRegex(ValueError, 'frame_length'):
                protocol.read_frame(stream)

    def test_truncated_body_never_becomes_success(self):
        with self.pipe(struct.pack('>I', 100) + b'{}') as stream:
            with self.assertRaisesRegex(EOFError, 'truncated_frame'):
                protocol.read_frame(stream)

    def test_silent_peer_has_a_deadline(self):
        read, write = os.pipe()
        try:
            with os.fdopen(read, 'rb', closefd=False) as stream:
                with self.assertRaisesRegex(TimeoutError, 'worker_frame_deadline'):
                    protocol.read_frame(stream, timeout=0.01)
        finally:
            os.close(read)
            os.close(write)
