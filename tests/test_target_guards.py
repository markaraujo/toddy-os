"""A workstation or unexpected root mount must be rejected before changes."""
from pathlib import Path
import subprocess
import unittest

GUARD = Path(__file__).resolve().parents[1] / 'scripts/build/target.sh'


class TargetGuards(unittest.TestCase):
    def guard(self, script):
        return subprocess.run(['bash', '-c', 'source "$1"; ' + script, 'guard', str(GUARD)],
                              capture_output=True, text=True)

    def test_wrong_hostname_rejected(self):
        result = self.guard('hostname() { echo unrelated-host; }; guard_guest')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Wrong guest hostname', result.stderr)

    def test_root_disk_cannot_be_target_mount(self):
        result = self.guard('guard_guest() { return 0; }; findmnt() { echo /dev/vda1; }; guard_target')
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
