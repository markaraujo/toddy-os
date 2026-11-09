"""Ensure console recovery accepts exact fragments while preserving report integrity."""
import base64
import hashlib
import json
from pathlib import Path
import random
import sys
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/host'))
from phase2_native_report import decode


class NativeReportIntegrity(unittest.TestCase):
    def transcript(self):
        data = {'kernel': 'fixture', 'bytes': random.Random(19).randbytes(6000).hex()}
        raw = json.dumps(data, sort_keys=True).encode()
        packed = base64.b64encode(zlib.compress(raw)).decode()
        chunks = [packed[i:i+1024] for i in range(0, len(packed), 1024)]
        lines = [f'TODDY_B02_RUNTIME_DATA {i} {chunk}' for i, chunk in enumerate(chunks)]
        lines.append('TODDY_B02_RUNTIME_RESULT ' + json.dumps({
            'chunks': len(chunks), 'report_sha256': hashlib.sha256(raw).hexdigest()}))
        return data, lines

    def test_exact_watchdog_split_rejoins_without_changing_payload(self):
        expected, lines = self.transcript()
        line = lines[0]
        lines[0] = line[:700] + '[   11.766230] clocksource: Watchdog remote CPU 10 read timed out\n' + line[700:]
        report, summary, recovered = decode('\n'.join(lines))
        self.assertEqual(report, expected)
        self.assertEqual(recovered[0]['payload_bytes_changed'], 0)
        self.assertGreater(summary['chunks'], 1)

    def test_unknown_console_noise_is_rejected(self):
        _, lines = self.transcript()
        lines[0] = lines[0][:700] + '[   11.766230] unknown console noise\n' + lines[0][700:]
        with self.assertRaises((AssertionError, ValueError)):
            decode('\n'.join(lines))

    def test_intact_base64_with_modified_bytes_is_rejected(self):
        _, lines = self.transcript()
        lines[1] = lines[1][:-1] + ('A' if lines[1][-1] != 'A' else 'B')
        with self.assertRaises((AssertionError, ValueError, zlib.error)):
            decode('\n'.join(lines))
