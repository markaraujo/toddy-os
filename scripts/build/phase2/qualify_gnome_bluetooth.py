"""Authenticate the two original core programs and preserve deferred integration."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gnome-bluetooth-47.2');w=Path('/mnt/lfs/sources/phase2/work/gnome-bluetooth-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='41f20e6d6176b72590af63552b232d83f2fffdd77ecfaa5eaf32c5a4a86fad64' and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']==digest(root/'scripts/build/phase2/gnome-bluetooth-build.sh')
 assert (l/'gnome-bluetooth-1.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert len(r['original_core_tests'])==2 and all(t['returncode']==0 and t['result']=='OK' for t in r['original_core_tests'])
 assert {t['name']:t['stdout'].count('\nok ') for t in r['original_core_tests']}=={'gnome-bluetooth:test-bluetooth-device-test':1,'gnome-bluetooth:test-bluetooth-device-utils':4}
 assert len(r['original_deferred_tests'])==15 and len(r['original_registered_tests'])==17
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 return r
