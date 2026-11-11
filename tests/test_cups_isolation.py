"""CUPS resolver extension must preserve the exact generic isolation profile."""
import importlib.util
from pathlib import Path
import unittest
import subprocess,tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('cups_isolation',ROOT/'scripts/build/phase2/cups_isolation.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class CupsIsolationTests(unittest.TestCase):
 def test_browser_tool_mounts_are_inactive_for_cups(self):
  source=(ROOT/'scripts/build/phase2/isolated.sh').read_text()
  start=source.index('# Browser-only private compiler tools:')
  end=source.index('# This selected TLS consumer',start)
  # An accidental compiler-tool bind must fail even without any VM paths.
  command='readonly_bind() { exit 97; };\n'+source[start:end]
  subprocess.run(['bash','-euc',command],env={'TODDY_INPUT':'/mnt/lfs/sources/phase2/inputs/cups-2.4.19','TODDY_WORK':'/mnt/lfs/sources/phase2/work/cups-1','PATH':'/usr/bin:/bin'},check=True)
 def test_changed_base_is_refused(self):
  with self.assertRaises(AssertionError):module.profile(b'changed generic sandbox')
 def test_only_private_public_hosts_extension_is_added(self):
  source=(ROOT/'scripts/build/phase2/isolated.sh').read_bytes();result=module.profile(source)
  self.assertIn('> "$root/etc/hosts"',result)
  self.assertNotIn('> /mnt/lfs/etc/hosts',result)
  self.assertIn('127.0.0.1 localhost toddy-builder',result)
  self.assertIn('::1 localhost toddy-builder',result)
  self.assertEqual(source,(ROOT/'scripts/build/phase2/isolated.sh').read_bytes())

 def test_effective_private_hosts_after_generic_initialization(self):
  source=(ROOT/'scripts/build/phase2/isolated.sh').read_bytes()
  result=module.profile(source)
  start=result.index("printf '127.0.0.1 localhost")
  end=result.index('# AccountsService',start)
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'etc').mkdir()
   subprocess.run(['bash','-euc',result[start:end]],env={'root':str(root),'TODDY_INPUT':'/mnt/lfs/sources/phase2/inputs/cups-2.4.19','PATH':'/usr/bin:/bin'},check=True)
   self.assertEqual((root/'etc/hosts').read_text(),'127.0.0.1 localhost toddy-builder\n::1 localhost toddy-builder\n')
   self.assertEqual((root/'etc/hosts').stat().st_mode&0o777,0o644)
