"""Exercise the actual Bash routing for private browser-tool exposure."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
PAIRS=[('/mnt/lfs/sources/phase2/inputs/firefox-153.2.0','/mnt/lfs/sources/phase2/work/firefox-build-1'),
       ('/mnt/lfs/sources/phase2/inputs/firefox-153.7.0','/mnt/lfs/sources/phase2/work/firefox-security-1537-1')]


class BrowserToolProfileTests(unittest.TestCase):
    def route(self,source,work):
        script=(ROOT/'scripts/build/phase2/isolated.sh').read_text()
        block=script[script.index('# Browser-only private compiler tools:'):script.index('# This selected TLS consumer')]
        with tempfile.TemporaryDirectory() as root:
            # These stubs observe branch routing only. Actual SDK/isolation proof
            # belongs to the native evidence, never this host fixture.
            stubs='python3() { printf "verified\\n"; }; readonly_bind() { printf "%s\\n" "$1"; };\n'
            return subprocess.check_output(['bash','-euc',stubs+block],text=True,
                env={'root':root,'TODDY_INPUT':source,'TODDY_WORK':work,'PATH':'/usr/bin:/bin'})

    def test_exact_paired_inputs_receive_only_qualified_private_tools(self):
        expected=['verified','/mnt/lfs/sources/phase2/work/firefox-1/tools/wasi-sdk-25.0-x86_64-linux',
                  '/mnt/lfs/sources/phase2/work/nasm-1/stage']
        for source,work in PAIRS:
            with self.subTest(source=source):self.assertEqual(self.route(source,work).splitlines(),expected)

    def test_mismatched_original_and_candidate_work_receives_no_tools(self):
        for index in [0,1]:
            with self.subTest(index=index):self.assertEqual(self.route(PAIRS[index][0],PAIRS[1-index][1]),'')
