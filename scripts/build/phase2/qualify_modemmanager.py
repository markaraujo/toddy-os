"""Bind actual local ModemManager tests, strict policy and immutable stage bytes."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/ModemManager-1.24.2');w=Path('/mnt/lfs/sources/phase2/work/modemmanager-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());locked=next(x for x in json.loads((root/'config/phase2/sources.lock.json').read_text())['components'] if x['name']=='modemmanager')
 assert p['source_sha256']==locked['sha256'] and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']==digest(root/'scripts/build/phase2/modemmanager-build.sh')
 assert (l/'modemmanager-1.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert len(r['original_tests'])==len(r['test_selection']['selected'])>=12 and all(t['returncode']==0 and t['result']=='OK' for t in r['original_tests'])
 assert set(r['test_selection']['deferred'])=={'test-at-serial-port','test-qcdm-serial-port','test-stub'}
 options={o['name']:o['value'] for o in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text())}
 assert options['polkit']=='strict' and all(options[n] for n in ['mbim','qmi','introspection','udev','systemd_suspend_resume','systemd_journal']) and not options['qrtr'] and not options['at_command_via_dbus']
 assert all(o['value']=='auto' for o in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text()) if o['name'].startswith('plugin_'))
 from shared_source_inputs import fingerprint,check_alias
 src=json.loads((l/'modemmanager-input-scratch-1.json').read_text());assert src['state']=='complete';check_alias(Path(src['source']),s);assert fingerprint(Path(src['source']))==src['source_fingerprint']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 return r
