"""Minimal revision4 source/refusal checks; no guest/native package writes."""
import hashlib,importlib.util,json,os,stat,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('installer4',ROOT/'scripts/build/phase2/installer_mvp_native.py')
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)
class Installer4Tests(unittest.TestCase):
 def test_only_exact_ubuntu_syslog_parent_is_allowed(self):
  group=p.grp.getgrnam('syslog').gr_gid
  row=SimpleNamespace(st_mode=stat.S_IFDIR|0o775,st_uid=0,st_gid=group)
  self.assertTrue(p.trusted_coherence_ancestor(Path('/var/log'),row))
  self.assertFalse(p.trusted_coherence_ancestor(Path('/var/log/toddy'),row))
  self.assertFalse(p.trusted_coherence_ancestor(Path('/var/log'),SimpleNamespace(st_mode=stat.S_IFDIR|0o777,st_uid=0,st_gid=group)))
 def test_runtime_source_map_includes_cross_directory_handoff_and_finalizer(self):
  with patch.object(p,'ROOT',ROOT):files=p.runtime_source_map()
  for name in ('runtime/installer/native_finalizer.py','scripts/build/phase2/offline_payload.py','runtime/setup/installer_handoff.py','runtime/shared/json.py'):
   self.assertEqual(files[name],p.digest(ROOT/name))
 def test_coherence_proof_requires_exact_current_map_and_verified_state(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);files={'runtime/installer/native_finalizer.py':'a'*64}
   sha=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()
   path=root/('input-source-coherence-'+sha+'.json')
   value={'version':1,'state':'required-source-bytes-verified','source_map_sha256':sha,'files':files}
   path.write_text(json.dumps(value));path.chmod(0o600)
   original=Path.lstat
   def root_metadata(self,*args,**kwargs):
    info=original(self,*args,**kwargs);row=list(info);row[4]=row[5]=0;row[0]&=~0o022;return os.stat_result(row)
   with patch.object(p,'BUILD',root),patch.object(p,'runtime_source_map',return_value=files),patch.object(Path,'lstat',root_metadata):
    self.assertEqual(p.runtime_coherence()['source_map_sha256'],sha)
    value['files']={'runtime/installer/native_finalizer.py':'b'*64};path.write_text(json.dumps(value))
    with self.assertRaisesRegex(ValueError,'coherence required'):p.runtime_coherence()


 def test_generation5_is_fixed_fresh_revision_and_preserves_compile3_defaults(self):
  original=(p.frozen.SOURCE,p.frozen.WORK,p.frozen.STEP,p.frozen.VERSION)
  try:
   p.configure(5)
   self.assertEqual(p.VERSION,'0.2.0-1+toddy3');self.assertEqual(p.STEP,'b12-toddy-installer-5')
   self.assertEqual(p.SOURCE.name,'toddy-installer-0.2.0-5');self.assertTrue(p.INSTALL.endswith('install5.sh'))
   with patch.object(p,'ROOT',ROOT):self.assertEqual(p.package().VERSION,'0.2.0-1+toddy3')
   self.assertEqual((p.frozen.SOURCE,p.frozen.WORK,p.frozen.STEP,p.frozen.VERSION),original)
   for invalid in (3,9,'5'):
    with self.assertRaises(ValueError):p.configure(invalid)
  finally:p.configure(4)


 def test_generation6_has_fresh_names_and_requires_actual_version3_baseline(self):
  try:
   p.configure(6)
   self.assertEqual(p.VERSION,'0.2.0-1+toddy4');self.assertEqual(p.BASELINE_VERSION,'0.2.0-1+toddy3')
   self.assertEqual(p.STEP,'b12-toddy-installer-6');self.assertTrue(p.CHECK.endswith('check6.sh'))
   self.assertEqual(p.PREPARED.name,'toddy-installer-prepared-6.json')
   with patch.object(p,'ROOT',ROOT):self.assertEqual(p.package().VERSION,'0.2.0-1+toddy4')
  finally:p.configure(4)

 def test_generation7_preserves_previous6_and_requires_coherence_before_native_action(self):
  try:
   p.configure(7)
   self.assertEqual(p.VERSION,'0.2.0-1+toddy5')
   self.assertEqual(p.BASELINE_VERSION,'0.2.0-1+toddy4')
   self.assertEqual(p.PREPARED.name,'toddy-installer-prepared-7.json')
   self.assertTrue(p.INSTALL.endswith('install7.sh'))
   self.assertTrue(p.CHECK.endswith('check7.sh'))
   with tempfile.TemporaryDirectory() as temporary,patch.object(p,'SOURCE',Path(temporary)/'absent'),patch.object(p,'WORK',Path(temporary)/'work'),patch.object(p,'STAGE',Path(temporary)/'stage'),patch.object(p,'PREPARED',Path(temporary)/'prepared'),patch.object(p,'RECEIPT',Path(temporary)/'receipt'),patch.object(p,'POSTCHECK_HOME',Path(temporary)/'postcheck'),patch.object(p,'runtime_coherence',side_effect=ValueError('coherence refusal')),patch.object(p.frozen,'native') as native,patch.object(p,'original_compile') as reuse:
    with self.assertRaisesRegex(ValueError,'coherence refusal'):p.prepare()
    native.assert_not_called();reuse.assert_not_called()
   with patch.object(p,'read',return_value={}),patch.object(p,'runtime_coherence',side_effect=ValueError('coherence refusal')),patch.object(p,'original_compile') as reuse:
    with self.assertRaisesRegex(ValueError,'coherence refusal'):p.qualify()
    reuse.assert_not_called()
  finally:p.configure(4)

 def test_generation8_uses_fresh_version_and_exact_previous7(self):
  try:
   p.configure(8)
   self.assertEqual(p.VERSION,'0.2.0-1+toddy6')
   self.assertEqual(p.BASELINE_VERSION,'0.2.0-1+toddy5')
   self.assertEqual(p.STEP,'b12-toddy-installer-8')
   self.assertTrue(p.INSTALL.endswith('install8.sh'))
   self.assertTrue(p.CHECK.endswith('check8.sh'))
  finally:p.configure(4)

 def test_generation7_previous_success_checks_actual_generation6_recipe(self):
  try:
   p.configure(7)
   success={'step':'b12-toddy-installer-6','recipe_exit':0,'postcheck_exit':0,'recipe_sha256':'unused'}
   def checked_digest(path):
    self.assertEqual(Path(path).name,'installer_mvp_install6.sh')
    raise ValueError('actual previous6 selected')
   with patch.object(p,'read',side_effect=[success,{},{},{}]),patch.object(p,'digest',side_effect=checked_digest):
    with self.assertRaisesRegex(ValueError,'actual previous6 selected'):p.previous_upgrade()
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
