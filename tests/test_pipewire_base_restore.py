"""Source-only exact recovery refusal fixtures; no actual Dpkg/APT operation."""
import copy,hashlib,importlib.util,json,os,subprocess,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('pipewire_base_restore',ROOT/'scripts/build/phase2/pipewire_base_restore.py')
p=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(p)

class RestoreTests(unittest.TestCase):
 def test_exact_eleven_additions_sorted_and_every_old_row_unchanged(self):
  old={'payload':{'/fixture/'+str(i):{'sha256':'a'*64} for i in range(649)}}
  expected={'/usr/bin/pw-cat'}|{'/usr/bin/'+name for name in p.frozen.ALIASES}|{'/usr/share/doc/pipewire/pw-cat-upgrade-source.json'}
  rejected={'payload':{**old['payload'],**{name:{'sha256':'b'*64} for name in expected}}}
  self.assertEqual(p.additions(old,rejected),sorted(expected))
  rejected['payload']['/fixture/1']={'sha256':'c'*64}
  with self.assertRaisesRegex(ValueError,'not_narrow'):p.additions(old,rejected)
  rejected=copy.deepcopy(old);rejected['payload']['/arbitrary']={}
  with self.assertRaises(ValueError):p.additions(old,rejected)
 def test_only_exact_known_five_apt_breakages_can_start_recovery(self):
  body='\n'.join(' '+name+' : Depends: pipewire (= 1.6.8-1+toddy1) but 1.6.8-1+toddy2 is installed' for name in p.REVERSE_PINS)+'\n'
  result=SimpleNamespace(returncode=100,stdout=body,stderr='fixture error')
  with patch.object(p.subprocess,'run',return_value=result) as run,patch.object(p,'APT_STDOUT_SHA',hashlib.sha256(body.encode()).hexdigest()),patch.object(p,'APT_STDERR_SHA',hashlib.sha256(result.stderr.encode()).hexdigest()):
   self.assertEqual(p.apt_before()['known_reverse_pins'],sorted(p.REVERSE_PINS));self.assertNotIn('--fix-broken',run.call_args.args[0])
   result.returncode=0
   with self.assertRaises(ValueError):p.apt_before()
   result.returncode=100;result.stdout+=' foreign : Depends: other\n'
   with self.assertRaises(ValueError):p.apt_before()
 def test_failed_custody_mismatch_refuses_before_any_native_install(self):
  with patch.object(p.frozen,'regular',side_effect=lambda path:path),patch.object(p.frozen,'digest',return_value='wrong'),patch.object(p,'PackageBackend') as backend:
   with self.assertRaisesRegex(ValueError,'custody_changed'):p.rejected()
   backend.assert_not_called()
 def test_direct_unprivileged_entry_has_no_native_side_effects(self):
  with patch.object(p.os,'getuid',return_value=1000),patch.object(p.sys,'argv',['restore','install']),patch.object(p.subprocess,'run') as run:
   with self.assertRaisesRegex(ValueError,'guest_root'):p.main()
   run.assert_not_called()
  for name in ('pipewire_base_restore_install.sh','pipewire_base_restore_check.sh'):subprocess.run(['/bin/bash','-n',str(ROOT/'scripts/build/phase2'/name)],check=True)

if __name__=='__main__':unittest.main()
