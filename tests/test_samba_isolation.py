"""The read-only Samba alias stays usable with the exact shared base."""
import importlib.util
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('samba_isolation',ROOT/'scripts/build/phase2/samba_isolation.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class SambaIsolationTests(unittest.TestCase):
    def test_current_exact_profile_and_readonly_alias(self):
        source=(ROOT/'scripts/build/phase2/isolated.sh').read_bytes()
        result=module.profile(source)
        self.assertIn(b'readonly_bind "$TODDY_WORK/probe-configured" "$root/src/bin"',result)
        self.assertNotIn(b'mount --rbind',result)

    def test_unknown_base_denied(self):
        with self.assertRaises(AssertionError):
            module.profile(b'unreviewed sandbox')

    def test_browser_tools_not_exposed_to_samba(self):
        source=(ROOT/'scripts/build/phase2/isolated.sh').read_text()
        block=source[source.index('# Browser-only private compiler tools:'):source.index('# This selected TLS consumer')]
        subprocess.run(['bash','-euc','readonly_bind() { exit 97; };\n'+block],
            env={'TODDY_INPUT':module.SOURCE,'TODDY_WORK':module.WORK,'PATH':'/usr/bin:/bin'},check=True)
