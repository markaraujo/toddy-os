"""Control-flow checks only; native APT repository acceptance remains separate."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AptWarningGuard(unittest.TestCase):
    def test_root_fallback_is_rejected_without_losing_other_exit_statuses(self):
        source = (ROOT / 'scripts/build/h07/apt-repository-check-inner.sh').read_text()
        function = 'apt-get() {' + source.split('apt-get() {', 1)[1].split('\n}', 1)[0] + '\n}'
        cases = [
            (0, 'Repository update completed', 0),
            (100, 'E: Hash Sum mismatch', 100),
            (0, "W: No sandbox user '_apt' on the system, can not drop privileges", 125),
            (0, 'W: Download is performed unsandboxed as root as file could not be accessed', 125),
            (100, 'W: Download is performed unsandboxed as root', 125),
        ]
        with tempfile.TemporaryDirectory() as directory:
            stub = Path(directory) / 'apt-get'
            stub.write_text('#!/bin/sh\nprintf "%s\\n" "$TODDY_TEST_APT_OUTPUT"\nexit "$TODDY_TEST_APT_EXIT"\n')
            stub.chmod(0o755)
            for code, output, expected in cases:
                with self.subTest(code=code, output=output):
                    result = subprocess.run(['/bin/bash', '-c', function + '\napt-get update'],
                        env={'PATH': directory + os.pathsep + os.defpath, 'fixture': directory,
                             'TODDY_TEST_APT_OUTPUT': output, 'TODDY_TEST_APT_EXIT': str(code)},
                        text=True, capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                    self.assertIn(output, result.stdout)


if __name__ == '__main__':
    unittest.main()
