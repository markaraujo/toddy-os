"""Small image-input provenance/account fixtures; no native preparation."""
import hashlib,importlib.util,stat,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts/build/phase2'))
import image_inputs as image
class ImageInputsTests(unittest.TestCase):
 def test_standard_signed_export2_is_preserved_while_mvp_requires_fresh7(self):
  for kind in ('base','live'):self.assertEqual(image.signed_export(kind).name,'toddy-package-export-2')
  for kind in ('mvp-base','mvp-live'):self.assertEqual(image.signed_export(kind).name,'toddy-package-export-8')
  with self.assertRaises(ValueError):image.signed_export('arbitrary')
 def test_cache_binding_covers_additional_namespace_and_carries_no_replay_claim(self):
  sha=lambda value:hashlib.sha256(value.encode()).hexdigest()
  path='/usr/share/glib-2.0/schemas/gschemas.compiled';tool='/usr/bin/glib-compile-schemas'
  reference='/usr/lib/gnome-terminal/gschemas.compiled'
  entries={reference:{'sha256':image.p.IMMUTABLE_SCHEMA_REFERENCES[reference]},path:{'sha256':sha('native cache')},tool:{'sha256':sha('tool')},
    '/usr/share/glib-2.0/schemas/base.gschema.xml':{'sha256':sha('base')},
    '/usr/share/glib-2.0/schemas/branding.gschema.override':{'sha256':sha('addition')}}
  record={'payload':{path:entries[path]}}
  with patch.object(image.p,'inventory',return_value={'entries':entries}):
   _,bindings,evidence=image.cache_bindings([record],{'native.json':sha('real record')})
  self.assertEqual(set(bindings[path]['inputs']),set(entries)-{path,tool,reference})
  self.assertNotIn(reference,bindings)
  self.assertFalse(evidence[path]['regeneration_passed'])
  self.assertEqual(bindings[path]['native_evidence_sha256'],hashlib.sha256(image.p.encoded(evidence[path])).hexdigest())
 def test_native_kmod_binding_uses_only_owned_regular_env_and_kmod(self):
  path='/usr/lib/modules/7.1.8-toddy/modules.dep'
  entries={'/usr/sbin/depmod':{'symlink':'../bin/kmod'},'/usr/bin/kmod':{'sha256':'a'*64},'/usr/bin/env':{'sha256':'b'*64}}
  self.assertEqual(image.cache_tool(path,entries),{'path':'/usr/bin/kmod','sha256':'a'*64})
  del entries['/usr/bin/env']
  with self.assertRaisesRegex(ValueError,'unavailable'):image.cache_tool(path,entries)
 def test_missing_selected_tool_refused(self):
  with self.assertRaisesRegex(ValueError,'unavailable'):image.cache_tool('/usr/share/glib-2.0/schemas/gschemas.compiled',{})
 def test_account_projection_strips_human_build_memberships_and_locks_all(self):
  passwd='root:x:0:0:root:/root:/bin/bash\nbuilder:x:101:101:Builder:/home/builder:/bin/bash\npolkitd:x:27:27:Policy:/:/usr/sbin/nologin\nowner:x:1000:1000:Owner:/home/owner:/bin/bash\n'
  groups='root:x:0:\nwheel:x:97:owner\nbuilder:x:101:builder\npolkitd:x:27:\nowner:x:1000:owner\n'
  entries={path:{'sha256':'a'*64} for path in ('/etc/pam.d/gdm-password','/usr/lib/systemd/system/gdm.service')}
  policy=image.account_policy(passwd,groups,entries)
  self.assertNotIn('owner',str(policy));self.assertNotIn('builder',str(policy))
  self.assertIn('wheel:x:97:\n',policy['accounts']['group'])
  generated=image.account_files(policy['accounts'])
  self.assertEqual(generated['etc/shadow'][0],b'root:!:::::::\npolkitd:!:::::::\n')
 def test_boot_profile_is_owned_exact_kernel_and_module_namespace(self):
  entries={'/boot/vmlinuz-7.1.8-toddy':{'sha256':'b'*64},'/usr/lib/modules/7.1.8-toddy/modules.builtin':{'sha256':'a'*64}}
  result=image.boot_profile(entries)
  self.assertEqual(result['kernel_sha256'],'b'*64);self.assertIn('ext4',result['modules'])
  with self.assertRaises(ValueError):image.boot_profile({})
