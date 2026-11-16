"""Unprivileged archive/stage fixtures only, no native package/audio qualification."""
import hashlib,importlib.util,io,json,os,subprocess,sys,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('pipewire_audio_tools',ROOT/'scripts/build/phase2/pipewire_audio_tools.py')
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)

class AudioToolsTests(unittest.TestCase):
 def test_packager_child_creates_public_control_without_relaxing_private_parent(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);previous=os.umask(0o077)
   try:
    p.run_packager([sys.executable,'-c',"from pathlib import Path;Path('DEBIAN').mkdir();Path('DEBIAN/control').write_text('public fixture')"],cwd=root)
    self.assertEqual((root/'DEBIAN').stat().st_mode&0o777,0o755)
    self.assertEqual((root/'DEBIAN/control').stat().st_mode&0o777,0o644)
    (root/'private-evidence').mkdir();self.assertEqual((root/'private-evidence').stat().st_mode&0o777,0o700)
   finally:os.umask(previous)
 def stage(self,root):
  bin=root/'usr/bin';bin.mkdir(parents=True);(bin/'pw-cat').write_bytes(b'explicit synthetic binary');(bin/'pw-cat').chmod(0o755)
  for alias in p.frozen.ALIASES:(bin/alias).symlink_to('pw-cat')
  doc=root/'usr/share/doc'/p.PACKAGE;doc.mkdir(parents=True)
  for name in ('copyright','source-manifest.json'):(doc/name).write_text('{}');(doc/name).chmod(0o644)
 def test_only_standalone_tool_alias_and_legal_namespace(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);self.stage(root);p.public_directories(root);observed=p.validate_stage(root)
   self.assertIn('usr/bin/pw-cat',observed['entries'])
   (root/'etc').mkdir();(root/'etc').chmod(0o755)
   with self.assertRaisesRegex(ValueError,'unselected_stage_directory'):p.validate_stage(root)
   (root/'etc').rmdir();(root/'usr/lib').mkdir();(root/'usr/lib/libpipewire.so').write_bytes(b'unselected')
   with self.assertRaises(ValueError):p.validate_stage(root)
 def test_private_umask_cannot_change_installed_usr_directory_modes(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);previous=os.umask(0o077)
   try:self.stage(root)
   finally:os.umask(previous)
   with self.assertRaisesRegex(ValueError,'public_directory_mode'):p.validate_stage(root)
   p.public_directories(root);p.validate_stage(root)
   self.assertTrue(all(path.stat().st_mode&0o777==0o755 for path in root.rglob('*') if path.is_dir()))
 def test_legal_copy_comes_from_old_archive_and_preserves_exact_bytes(self):
  data=b'Exact source notice fixture\n';raw=io.BytesIO();rows={}
  with tarfile.open(fileobj=raw,mode='w') as archive:
   for name in ('copyright','source-notices/index.json'):
    virtual='/usr/share/doc/pipewire/'+name;member=tarfile.TarInfo('.'+virtual);member.size=len(data);member.mode=0o644;member.uid=member.gid=0;archive.addfile(member,io.BytesIO(data))
    rows[virtual]={'mode':0o100644,'uid':0,'gid':0,'sha256':hashlib.sha256(data).hexdigest()}
  with tempfile.TemporaryDirectory() as temporary,patch.object(p.subprocess,'check_output',return_value=raw.getvalue()),patch.object(p.frozen,'digest',return_value=p.frozen.OLD_ARCHIVE_SHA):
   root=Path(temporary);copied=p.legal_from_archive(root,{'payload':rows},Path('/fixture/old.deb'))
   self.assertEqual(len(copied),2);self.assertEqual((root/'usr/share/doc'/p.PACKAGE/'copyright').read_bytes(),data)
   self.assertFalse((root/'usr/share/doc/pipewire').exists())
 def test_per_file_headers_are_read_from_verified_private_source_archive(self):
  raw=io.BytesIO()
  with tarfile.open(fileobj=raw,mode='w') as archive:
   for name in p.HEADER_SOURCES:
    data=b'/* SPDX-License-Identifier: MIT */\npublic fixture source\n';member=tarfile.TarInfo('pipewire-1.6.8/src/tools/'+name);member.size=len(data);archive.addfile(member,io.BytesIO(data))
  with tempfile.TemporaryDirectory() as temporary:
   source=Path(temporary)/'source.tar';source.write_bytes(raw.getvalue())
   with patch.object(p.frozen,'verified_source',return_value=(source,{'fixture':'unqualified'})):
    selected=p.header_data();self.assertEqual(set(selected),set(p.HEADER_SOURCES))
    output=Path(temporary)/'stage';output.mkdir();proof=p.retained_headers(output,selected);self.assertEqual(len(proof),11)
 def test_recovery_required_before_native_package_mutation(self):
  with patch.object(p,'transaction'),patch.object(p,'restoration',side_effect=ValueError('actual restore missing')),patch.object(p.subprocess,'run') as run,patch.object(p.frozen,'qualify') as build:
   with self.assertRaisesRegex(ValueError,'restore missing'):p.install()
   run.assert_not_called();build.assert_not_called()
 def test_upstream_revision_preserved_no_recompile_or_provides_retarget(self):
  source=(ROOT/'scripts/build/phase2/pipewire_audio_tools.py').read_text()
  self.assertIn('frozen.qualify()',source);self.assertNotIn('meson setup',source);self.assertNotIn("'--provides'",source)
  self.assertIn('pipewire (= 1.6.8-1+toddy1)',p.DEPENDS);self.assertEqual(p.VERSION,'1.6.8-1+toddy1')
  for name in ('pipewire_audio_tools_install.sh','pipewire_audio_tools_check.sh'):subprocess.run(['/bin/bash','-n',str(ROOT/'scripts/build/phase2'/name)],check=True)

if __name__=='__main__':unittest.main()
