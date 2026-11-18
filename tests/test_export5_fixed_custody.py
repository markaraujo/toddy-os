"""Fixed export5 slot/restore fixtures, no native or signing operation."""
import sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts/host'),str(ROOT/'scripts/build/phase2')]
import collect_package_export2 as collect
import stage_package_export3_signatures as host
import export4_public_signatures as native
class Export5Tests(unittest.TestCase):
 def test_only_explicit_fresh5_paths_preserve_old_defaults(self):
  self.assertEqual(collect.fixed_paths(5),('/mnt/lfs/sources/stage/toddy-package-export-5',ROOT/'.local/phase2/mvp-package-export-5'))
  self.assertEqual(host.fixed_context(5),ROOT/'.local/phase2/mvp-package-export-5')
  paths=native.fixed_paths(5)
  self.assertEqual(paths[0].name,'toddy-package-export-5');self.assertEqual(paths[1].name,'package-export5-public-signatures-1.json')
  self.assertEqual(paths[2].name,'toddy-export5-public-verification-1')
  self.assertEqual(native.fixed_paths(),(native.EXPORT,native.RECEIPT,native.RUN))
  self.assertEqual(host.fixed_context(),host.CONTEXT);self.assertEqual(collect.fixed_paths(),(collect.SOURCE,collect.DESTINATION))
  for value in (3,7,'5'):
   with self.assertRaises(ValueError):native.fixed_paths(value)
  self.assertEqual(collect.fixed_paths(6),('/mnt/lfs/sources/stage/toddy-package-export-6',ROOT/'.local/phase2/mvp-package-export-6'))
  self.assertEqual(host.fixed_context(6),ROOT/'.local/phase2/mvp-package-export-6')
  self.assertEqual(native.fixed_paths(6)[0].name,'toddy-package-export-6')
 def test_export5_failure_restores_export3_and_stream_globals(self):
  before=(native.base.EXPORT,native.base.RECEIPT,native.base.RUN,native.base.verify_command,native.base.save,native.stream.RUN)
  def fail(raw):
   self.assertEqual((native.base.EXPORT,native.base.RECEIPT,native.base.RUN),native.fixed_paths(5))
   self.assertEqual(native.stream.RUN,native.fixed_paths(5)[2])
   raise ValueError('fixture stopped before any filesystem write')
  with patch.object(native.base,'stage',side_effect=fail):
   with self.assertRaisesRegex(ValueError,'fixture stopped'):native.stage(b'public fixture',5)
  self.assertEqual((native.base.EXPORT,native.base.RECEIPT,native.base.RUN,native.base.verify_command,native.base.save,native.stream.RUN),before)
