"""Live installer source/stage contracts; not native Qt/root-GUI acceptance."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.build.phase2 import installer_package as package
from scripts.build.phase2 import installer_native as native
from runtime.installer import launch
from runtime.installer.disk_plan import InstallError

ROOT=Path(__file__).resolve().parents[1]

class InstallerPackageTests(unittest.TestCase):
 def test_payload_plan_is_live_only_fixed_paths_and_no_qualification_or_fixture_inputs(self):
  inputs,files,links=package.plan(ROOT)
  self.assertIn('/usr/bin/toddy-installer',files)
  self.assertIn('/usr/libexec/toddy-installer-auth',files)
  self.assertNotIn('/usr/lib/toddy/__init__.py',files)
  self.assertFalse(any(name.startswith('/etc/calamares/') for name in files))
  self.assertFalse(any('/composition/' in name or name.endswith('/launch-qualification.json') for name in files))
  self.assertFalse(any('fixtures/' in name or name.endswith('qualification.py') for name in inputs))
  self.assertIn(b'NoDisplay=true',files['/usr/share/applications/io.github.markaraujo.Toddy.Installer.desktop'][0])
  self.assertIn(b'auth_admin',files['/usr/share/polkit-1/actions/io.github.markaraujo.Toddy.Install.policy'][0])
  self.assertNotIn(b'exec.allow_gui',files['/usr/share/polkit-1/actions/io.github.markaraujo.Toddy.Install.policy'][0])
  self.assertNotIn(b'\n- exec:',files['/usr/share/toddy/installer/calamares-qualification/settings.conf'][0])
  self.assertEqual(set(links.values()),{'../../../../calamares/branding/toddy'})
  self.assertEqual(files['/usr/lib/toddy/installer/offline_payload.py'][0],(ROOT/'scripts/build/phase2/offline_payload.py').read_bytes())
  self.assertEqual(files['/usr/lib/toddy/installer/h10/initramfs_archive.py'][0],(ROOT/'scripts/build/h10/initramfs_archive.py').read_bytes())

 def test_missing_or_non_native_artifact_never_creates_product_stage(self):
  with tempfile.TemporaryDirectory() as temporary:
   base=Path(temporary);module=base/'fixture.so';receipt=base/'fixture.json';receipt.write_text('{}')
   with self.assertRaises(package.InstallerPackageError):package.stage(ROOT,base/'output',module,receipt)
   self.assertFalse((base/'output').exists())
   module.write_bytes(b'explicit unit fixture; not an ELF module')
   with self.assertRaisesRegex(package.InstallerPackageError,'native_amd64'):package.stage(ROOT,base/'output',module,receipt)
   self.assertFalse((base/'output').exists())

 def test_actual_installed_namespace_source_fixture_imports_without_optional_agent(self):
  # Private source-layout fixture only, deliberately no module or native receipt;
  # package.stage correctly refuses to call this a built product package.
  with tempfile.TemporaryDirectory() as temporary:
   base=Path(temporary);prefix=base/'usr/lib/toddy';prefix.mkdir(parents=True)
   (prefix/'__init__.py').write_text('')
   for child in ('setup','shared'):
    shutil.copytree(ROOT/'runtime'/child,prefix/child,ignore=shutil.ignore_patterns('__pycache__'))
   _,files,_=package.plan(ROOT)
   for absolute,(data,mode) in files.items():
    path=base/absolute.lstrip('/');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(mode)
   code='''
import sys
sys.path.insert(0,sys.argv[1])
from toddy.installer.live_bindings import create
from toddy.installer.disk_plan import InstallError
from toddy.installer.installed_boot import init_script
from toddy.setup.installer_handoff import save
try:create()
except InstallError as error:assert str(error)=='installer_composed_closure_unavailable'
else:raise AssertionError('unqualified-source-fixture-authorized')
assert 'toddy.broker' not in sys.modules and 'toddy.executor' not in sys.modules
assert b'mount -t ext4' in init_script('abcd-1234',['ext4','virtio_blk'])
print('SOURCE_LAYOUT_IMPORT_ONLY_NO_NATIVE_PACKAGE_OR_GUI')
'''
   result=subprocess.run([sys.executable,'-I','-c',code,str(base/'usr/lib')],capture_output=True,text=True,timeout=10,cwd=base)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertIn('SOURCE_LAYOUT_IMPORT_ONLY',result.stdout)

 def test_logind_session_scope_refuses_remote_locked_wrong_owner_or_wrong_class(self):
  good={'User':(1000,'/user'),'Active':True,'Remote':False,'LockedHint':False,'Type':'wayland','Class':'user','State':'active'}
  launch.validate_session(1000,good)
  for changed in ({'User':(1001,'/user')},{'User':()},{'Active':False},{'Remote':True},{'LockedHint':True},{'Type':'x11'},{'Class':'greeter'}):
   with self.subTest(changed=changed),self.assertRaises(InstallError):launch.validate_session(1000,{**good,**changed})

 def test_actual_private_fixture_socket_requires_owner_mode_name_and_no_symlink(self):
  with tempfile.TemporaryDirectory() as temporary:
   base=Path(temporary);directory=base/str(os.getuid());directory.mkdir(mode=0o700)
   path=directory/'wayland-7';server=socket.socket(socket.AF_UNIX)
   self.addCleanup(server.close);server.bind(str(path));path.chmod(0o600)
   def fixture_path(value):return base if value=='/run/user' else Path(value)
   with patch.object(launch,'Path',side_effect=fixture_path):
    self.assertEqual(launch.validate_socket(os.getuid(),'wayland-7'),(directory,path))
    with self.assertRaises(InstallError):launch.validate_socket(os.getuid(),'../wayland-7')
    directory.chmod(0o755)
    with self.assertRaises(InstallError):launch.validate_socket(os.getuid(),'wayland-7')
    directory.chmod(0o700);server.listen(1);launch.verify_peer(path,os.getuid())
    path.unlink();path.symlink_to(directory/'not-a-socket')
    with self.assertRaises(InstallError):launch.validate_socket(os.getuid(),'wayland-7')

 def test_closed_gui_environment_never_inherits_session_credentials_or_loader_values(self):
  with patch.dict(os.environ,{'DBUS_SESSION_BUS_ADDRESS':'PRIVATE-FIXTURE','LD_PRELOAD':'PRIVATE-FIXTURE','TOKEN':'PRIVATE-FIXTURE'}):
   value=launch.clean_environment(Path('/run/user/1000'),Path('/run/toddy-installer/gui-fixture'),'wayland-7','pt_BR.UTF-8')
  self.assertFalse(set(value)&{'DBUS_SESSION_BUS_ADDRESS','LD_PRELOAD','TOKEN','DISPLAY','XAUTHORITY','PYTHONPATH'})
  self.assertEqual(value['QT_QPA_PLATFORM'],'wayland');self.assertEqual(value['LANG'],'pt_BR.UTF-8')

 def test_qualification_source_driver_cannot_be_selected_by_factory_or_polkit(self):
  source=(ROOT/'scripts/build/phase2/installer_qualification.py').read_text()
  self.assertIn('QualificationPolicy(args.serial)',source)
  self.assertIn('validate_owner_options(inputs.policy',source)
  self.assertNotIn('--test',package.ROOT_ENTRY)
  self.assertNotIn('qualification',package.POLICY)
  self.assertNotIn('installer_qualification', (ROOT/'runtime/installer/live_bindings.py').read_text())

 def test_untrusted_stage_manifest_refuses_symlink_oversize_duplicate_or_nonfinite_data(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);stage=root/'stage';leaf=stage/'usr/share/doc/toddy-installer/source-manifest.json';leaf.parent.mkdir(parents=True)
   leaf.write_text('{"scope":"plain private parser fixture"}')
   self.assertEqual(native.read_stage_manifest(stage)['scope'],'plain private parser fixture')
   for data in (b'{"x":1,"x":2}',b'{"x":NaN}'):
    leaf.write_bytes(data)
    with self.assertRaises(ValueError):native.read_stage_manifest(stage)
   with leaf.open('wb') as stream:stream.truncate(2*1024*1024+1)
   with self.assertRaises(ValueError):native.read_stage_manifest(stage)
   leaf.unlink();outside=root/'outside';outside.write_text('NEVER-READ-fixture')
   leaf.symlink_to(outside)
   with self.assertRaises(ValueError):native.read_stage_manifest(stage)

 def test_source_inventory_allows_only_exact_declared_brand_dependency_alias(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);document=root/'usr/share/doc/toddy-installer/source-manifest.json';document.parent.mkdir(parents=True)
   file=root/'usr/share/source-fixture.txt';file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'unit fixture, no native module');file.chmod(0o644)
   alias=root/'usr/share/toddy/installer/calamares/branding/toddy';alias.parent.mkdir(parents=True)
   target='../../../../calamares/branding/toddy';alias.symlink_to(target)
   manifest={'scope':'unit-source-inventory-not-a-native-package','files':{'/usr/share/source-fixture.txt':{'sha256':native.digest(file),'mode':'0644'}},
             'dependency_links':{'/usr/share/toddy/installer/calamares/branding/toddy':target},'live_only':True,'offline_base':False,'native_root_gui_qualified':False}
   document.write_text(json.dumps(manifest));native.inventory(root)
   alias.unlink();alias.symlink_to('/unexpected/private-target')
   with self.assertRaisesRegex(ValueError,'unknown_dependency_link'):native.inventory(root)

 def test_direct_provider_ownership_and_recipe_identity_refuse_before_package_writes(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);target=root/'target';stage=root/'stage';library=target/'usr/lib/libc.so.6';library.parent.mkdir(parents=True);library.write_bytes(b'fixture provider')
   info=target/'var/lib/dpkg/info';info.mkdir(parents=True);(info/'glibc.list').write_text('/usr/lib/libc.so.6\n')
   stage.mkdir();(stage/'fixture-module').write_bytes(b'\x7fELF')
   with patch.object(native,'TARGET',target),patch.object(native.subprocess,'check_output',return_value='0 (NEEDED) Shared library: [libc.so.6]\n'):
    self.assertEqual(native.elf_dependencies(stage)['elf_files'],1)
    (info/'unapproved.list').write_text('/usr/lib/libc.so.6\n')
    with self.assertRaisesRegex(ValueError,'undeclared_native'):native.elf_dependencies(stage)
   marker=root/'build'/ (native.STEP+'.running.json');marker.parent.mkdir()
   value={'step':native.STEP,'user':'root','recipe_sha256':'a'*64,'postcheck_sha256':'a'*64,'recipe_pid':os.getpid()}
   marker.write_text(json.dumps(value))
   def fixture_path(path):return marker.parent if path=='/var/log/toddy/build' else Path(path)
   with patch.object(native,'Path',side_effect=fixture_path),patch.object(native,'digest',return_value='a'*64):
    native.transaction('install');value['recipe_pid']=-1;marker.write_text(json.dumps(value))
    with self.assertRaises(ValueError):native.transaction('install')
    value.update(recipe_exit=0,step='unrelated');marker.write_text(json.dumps(value))
    with self.assertRaises(ValueError):native.transaction('postcheck')

if __name__=='__main__':unittest.main()
