"""Source contracts only; no native disk/root installation or boot claim."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from runtime.installer.live_bindings import create
from runtime.installer.disk_plan import InstallError
from runtime.installer.installed_boot import init_script,module_namespace,InstalledBoot
from runtime.installer.native_finalizer import account_files,cache_command,cache_executables,verify_cache_executables
from runtime.installer.composition import validate_boot_evidence,validate_finalizer_report,ComposedPayload,bundle_namespace,secured,validate_owner_options
from runtime.setup.installer_handoff import save

ROOT=Path(__file__).resolve().parents[1]

class LiveBindingsTests(unittest.TestCase):
 def test_factory_missing_fixed_qualified_composition_never_dispatches(self):
  with patch('runtime.installer.linux_disk.LinuxDisk.run',side_effect=AssertionError('native-dispatch')):
   with self.assertRaisesRegex(InstallError,'composed_closure_unavailable'):create()

 def test_installed_init_is_literal_uuid_bounded_storage_only_and_valid_shell(self):
  script=init_script('abcd-1234',['ext4','virtio_pci','virtio_blk'])
  parsed=subprocess.run(['/bin/bash','-n'],input=script,capture_output=True,timeout=5)
  self.assertEqual(parsed.returncode,0,parsed.stderr)
  self.assertIn(b'attempt<60',script);self.assertIn(b'mount -t ext4 -o ro',script)
  self.assertIn(b'/usr/lib/systemd/systemd',script)
  self.assertNotIn(b'/proc/cmdline',script);self.assertNotIn(b'overlay',script.split(b'export PATH',1)[1])
  for uuid,modules in [('abcd;reboot',['ext4','virtio_blk']),('abcd',['ext4','shell']),('abcd',['ext4']),('abcd',['ext4','virtio_blk','ext4'])]:
   with self.assertRaises(InstallError):init_script(uuid,modules)

 def test_module_namespace_and_kernel_profile_cannot_be_substituted(self):
  entries={'/usr/lib/modules/7.1.8-toddy':{'directory':True},'/usr/lib/modules/7.1.8-toddy/modules.builtin':{'sha256':'a'*64},'/boot/vmlinuz-7.1.8-toddy':{'sha256':'b'*64}}
  selected,digest=module_namespace(entries)
  self.assertEqual(len(selected),2)
  profile={'kernel_sha256':'b'*64,'module_namespace_sha256':digest,'modules':['ext4','virtio_blk'],'epoch':0}
  InstalledBoot(Path('/fixture-only'),{'ownership':{'entries':entries}},profile,None)
  for changed in ({**profile,'kernel_sha256':'c'*64},{**profile,'module_namespace_sha256':'d'*64}):
   with self.assertRaises(InstallError):InstalledBoot(Path('/fixture-only'),{'ownership':{'entries':entries}},changed,None)

 def test_fresh_locked_account_policy_rejects_builder_hashes_or_extra_root(self):
  source=json.loads((ROOT/'config/live-account-baseline.json').read_bytes());baseline={key:source[key] for key in ('passwd','group')}
  files=account_files(baseline)
  self.assertEqual(files['etc/machine-id'][0],b'')
  self.assertTrue(all(row.split(b':')[1]==b'!' for row in files['etc/shadow'][0].splitlines()))
  for addition in ('builder:x:1000:999:Builder:/home/builder:/bin/bash\n','other:x:0:0:root:/root:/bin/bash\n','bad:$hash:101:100:bad:/:/usr/bin/false\n'):
   with self.assertRaises(InstallError):account_files({**baseline,'passwd':baseline['passwd']+addition})

 def test_frozen_kmod_argv0_and_both_regular_executable_custody(self):
  import tempfile,hashlib
  path='/usr/lib/modules/7.1.8-toddy/modules.dep';tool='/usr/bin/kmod'
  self.assertEqual(cache_command(path,tool),['/usr/bin/env','--argv0=depmod',tool,'-a','7.1.8-toddy'])
  self.assertEqual(cache_executables(path,tool),['/usr/bin/env',tool])
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);(root/'usr/bin').mkdir(parents=True)
   entries={}
   for name in ('env','kmod'):
    file=root/'usr/bin'/name;file.write_bytes(name.encode());entries['/usr/bin/'+name]={'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
   binding={'tool':{'path':tool,'sha256':entries[tool]['sha256']}}
   verify_cache_executables(root,path,binding,entries)
   file=root/'usr/bin/env';file.unlink();file.symlink_to('kmod')
   with self.assertRaisesRegex(ValueError,'cache_tool_changed'):verify_cache_executables(root,path,binding,entries)
   file.unlink();file.write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'cache_tool_changed'):verify_cache_executables(root,path,binding,entries)

 def test_cache_argv_is_fixed_and_unknown_recipe_refuses(self):
  self.assertEqual(cache_command('/usr/share/glib-2.0/schemas/gschemas.compiled','/usr/bin/glib-compile-schemas'),['/usr/bin/glib-compile-schemas','--strict','/usr/share/glib-2.0/schemas'])
  for path,tool in [('/usr/share/icons/../bad/icon-theme.cache','/usr/bin/gtk-update-icon-cache'),('/usr/share/glib-2.0/schemas/gschemas.compiled','/tmp/run-hook'),('/unknown','/usr/bin/true')]:
   with self.assertRaises(ValueError):cache_command(path,tool)

 def test_boot_qualification_requires_distinct_detached_persistent_boots(self):
  descriptor={'payload_manifest_sha256':'a'*64,'image_manifest_sha256':'b'*64,'source_sha256':{'installed_boot.py':'c'*64}}
  boot={'kernel_sha256':'d'*64}
  first={'boot_id':'11111111-1111-1111-1111-111111111111','root_uuid':'abcd-1234','persistent_marker_sha256':'e'*64,'kernel_release':'7.1.8-toddy','installer_media_attached':False,'fresh_owner_login':True,'initramfs_sha256':'f'*64}
  value={'kind':'native-detached-installed-boot-v1','firmware':'bios','input_manifest_sha256':'a'*64,'image_manifest_sha256':'b'*64,'kernel_sha256':'d'*64,'initramfs_source_sha256':'c'*64,'boots':[first,{**first,'boot_id':'22222222-2222-2222-2222-222222222222'}]}
  validate_boot_evidence(value,'bios',descriptor,boot)
  for change in ({'installer_media_attached':True},{'boot_id':first['boot_id']},{'persistent_marker_sha256':'f'*64}):
   changed=copy.deepcopy(value);changed['boots'][1].update(change)
   with self.assertRaises(InstallError):validate_boot_evidence(changed,'bios',descriptor,boot)

 def test_real_user_pendingstore_handoff_records_only_deferred_intent(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);catalog=ROOT/'config/phase2/software-catalog.json'
   request={'operation_id':'a'*32,'uid':os.getuid(),'gid':os.getgid(),'username':'fixture-owner','ai_choice':'local','extras':['docker','vscode'],'catalog_sha256':hashlib.sha256(catalog.read_bytes()).hexdigest()}
   result=save(request,home=root,catalog_path=catalog)
   pending=root/'.local/state/toddy/setup/pending.json'
   value=json.loads(pending.read_bytes())
   self.assertEqual(result['manifest_sha256'],hashlib.sha256(pending.read_bytes()).hexdigest())
   self.assertEqual(pending.stat().st_uid,os.getuid());self.assertEqual(pending.stat().st_mode&0o777,0o600)
   self.assertEqual(value['consent_receipts'],[])
   self.assertTrue(all(row['state']=='deferred' and row['artifact_id'] is None for row in value['choices']))
   with self.assertRaises(ValueError):save(request,home=root,catalog_path=catalog)

 def test_bare_passed_markers_cannot_replace_native_finalizer_measurements(self):
  descriptor={'payload_manifest_sha256':'a'*64,'image_manifest_sha256':'b'*64}
  value={'check':'whole-image-attribution','input_manifest_sha256':'a'*64,'passed':True,'exit_status':0,'postconditions':{'verified':True}}
  with self.assertRaises(InstallError):validate_finalizer_report(value,'whole-image-attribution',descriptor)
  value['postconditions']={'image_manifest_sha256':'b'*64,'entries':10}
  validate_finalizer_report(value,'whole-image-attribution',descriptor)
  value['postconditions']['image_manifest_sha256']='c'*64
  with self.assertRaises(InstallError):validate_finalizer_report(value,'whole-image-attribution',descriptor)

 def test_owner_system_identity_collision_is_refused_before_payload_dispatch(self):
  from types import SimpleNamespace
  native=SimpleNamespace(verify_payload=lambda _:self.fail('payload-dispatched'))
  composition=SimpleNamespace(readiness=lambda:None,policy={'accounts':{'passwd':'_apt:x:100:100:APT:/:/usr/bin/false\n','group':'_apt:x:100:\n'}})
  payload=ComposedPayload(composition,native)
  with self.assertRaisesRegex(InstallError,'installer_owner'):
   payload.verify_payload({'options':{'username':'owner','uid':1000,'gid':100}})

 def test_pending_handoff_rejects_extra_secret_field_and_redirected_parent_before_write(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);catalog=ROOT/'config/phase2/software-catalog.json'
   request={'operation_id':'a'*32,'uid':os.getuid(),'gid':os.getgid(),'username':'fixture-owner','ai_choice':'later','extras':[],
            'catalog_sha256':hashlib.sha256(catalog.read_bytes()).hexdigest()}
   with self.assertRaises(ValueError):save({**request,'password':'NEVER-ACCEPTED-FIXTURE'},home=root,catalog_path=catalog)
   self.assertFalse((root/'.local').exists())
   elsewhere=root/'elsewhere';elsewhere.mkdir();(root/'.local').symlink_to(elsewhere)
   with self.assertRaises(ValueError):save(request,home=root,catalog_path=catalog)
   self.assertEqual(list(elsewhere.iterdir()),[])

 def test_offline_bundle_refuses_unsigned_extra_credentials_or_cache_namespaces(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary)
   for name in ('archives','records','repository'):(root/name).mkdir()
   for name in ('manifest.json','preparation-state.json','profile.json','projection.json','catalog.json',
                'repository/trusted-keyring.gpg','repository/Release','repository/Release.gpg','repository/Packages',
                'archives/fixture.deb','records/fixture.json'):(root/name).write_bytes(b'explicit-test-only')
   manifest={'components':[{'archive':'fixture.deb','record':'fixture.json'}]}
   bundle_namespace(root,manifest)
   (root/'repository/private-key.asc').write_bytes(b'NOT-A-KEY-test-only-forbidden-name')
   with self.assertRaisesRegex(InstallError,'unselected_payload_state'):bundle_namespace(root,manifest)
   (root/'repository/private-key.asc').unlink();(root/'archives/cache').mkdir()
   with self.assertRaisesRegex(InstallError,'unselected_payload_state'):bundle_namespace(root,manifest)

 def test_review_owner_namespace_uses_authoritative_policy_and_dispatches_nothing(self):
  policy={'accounts':{'passwd':'root:x:0:0:root:/root:/bin/bash\nbin:x:1:1:bin:/:/usr/bin/false\ngdm:x:1001:1001:GDM:/:/usr/bin/false\n',
                      'group':'root:x:0:\nwheel:x:97:\ngdm:x:1001:\n'}}
  validate_owner_options(policy,{'username':'fresh-owner','uid':1000,'gid':1000})
  for options in ({'username':'wheel','uid':1000,'gid':1000},{'username':'gdm','uid':1000,'gid':1000},
                  {'username':'bin','uid':1000,'gid':1000},{'username':'owner','uid':1001,'gid':1000},
                  {'username':'owner','uid':1000,'gid':1001},{'username':'tester','uid':1000,'gid':1000}):
   with self.subTest(options=options),self.assertRaises(InstallError):validate_owner_options(policy,options)

if __name__=='__main__':unittest.main()
