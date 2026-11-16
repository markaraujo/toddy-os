"""Minimal revision4 source/refusal checks; no guest/native package writes."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('installer4',ROOT/'scripts/build/phase2/installer_mvp_native.py')
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)
class Installer4Tests(unittest.TestCase):
 def test_generation5_is_fixed_fresh_revision_and_preserves_compile3_defaults(self):
  original=(p.frozen.SOURCE,p.frozen.WORK,p.frozen.STEP,p.frozen.VERSION)
  try:
   p.configure(5)
   self.assertEqual(p.VERSION,'0.2.0-1+toddy3');self.assertEqual(p.STEP,'b12-toddy-installer-5')
   self.assertEqual(p.SOURCE.name,'toddy-installer-0.2.0-5');self.assertTrue(p.INSTALL.endswith('install5.sh'))
   with patch.object(p,'ROOT',ROOT):self.assertEqual(p.package().VERSION,'0.2.0-1+toddy3')
   self.assertEqual((p.frozen.SOURCE,p.frozen.WORK,p.frozen.STEP,p.frozen.VERSION),original)
   for invalid in (3,6,'5'):
    with self.assertRaises(ValueError):p.configure(invalid)
  finally:p.configure(4)


 def test_private_revision_generator_keeps_original_frozen_version(self):
  with patch.object(p,'ROOT',ROOT):pkg=p.package()
  self.assertEqual(pkg.VERSION,'0.2.0-1+toddy2')
  self.assertEqual(p.frozen.package_module().VERSION,'0.2.0-1+toddy1')
  self.assertNotEqual(p.STAGE,p.frozen.STAGE);self.assertNotEqual(p.PREPARED,p.frozen.PREPARED)
  self.assertNotEqual(p.RECEIPT,p.frozen.RECEIPT);self.assertNotEqual(p.STEP,p.frozen.STEP)
 def test_existing_preparation_refused_before_reuse_or_any_write(self):
  with tempfile.TemporaryDirectory() as temporary,patch.object(p,'PREPARED',Path(temporary)/'prepared.json'),patch.object(p,'original_compile') as reuse:
   p.PREPARED.write_text('interrupted')
   with self.assertRaisesRegex(ValueError,'no replay'):p.prepare()
   reuse.assert_not_called()
 def test_source_cpp_change_refuses_before_stage_copy(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);source=root/'old';source.mkdir();work=root/'work';work.mkdir();current=root/'current';current.mkdir()
   file='runtime/installer/calamares/CMakeLists.txt'
   for base,data in ((source/'repository','frozen'),(current,'changed')):
    path=base/file;path.parent.mkdir(parents=True);path.write_text(data)
   harness=current/'scripts/build/phase2/isolated.sh';harness.parent.mkdir(parents=True);harness.write_text('frozen harness')
   prepared={'state':'prepared','before':{},'harness_sha256':p.digest(harness),'source_inode':source.stat().st_ino,'work_inode':work.stat().st_ino,'inputs':{file:p.digest(source/'repository'/file)}}
   with patch.object(p,'ROOT',current),patch.object(p.frozen,'SOURCE',source),patch.object(p.frozen,'WORK',work),patch.object(p.frozen,'package_state',return_value={}),patch.object(p,'read',side_effect=[prepared,{}]),patch.object(p.frozen,'package_module',return_value=type('Pkg',(),{'COMPILE_INPUTS':('CMakeLists.txt',)})()):
    with self.assertRaisesRegex(ValueError,r'C\+\+ input differs'):p.original_compile()
 def test_private_receipts_keep_interrupted_part_and_never_overwrite_it(self):
  with tempfile.TemporaryDirectory() as temporary:
   path=Path(temporary)/'receipt.json';p.save(path,{'state':'preparing'})
   self.assertEqual(path.stat().st_mode&0o777,0o600)
   path.with_suffix('.part').write_text('interrupted')
   with self.assertRaises(FileExistsError):p.save(path,{'state':'complete'})
   self.assertEqual(json.loads(path.read_text())['state'],'preparing')
