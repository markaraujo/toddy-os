"""Authenticate GSound compile/stage and explicit original-suite absence."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gsound-1.0.3');w=Path('/mnt/lfs/sources/phase2/work/gsound-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='ca2d039e1ebd148647017a7f548862350bc9af01986d39f10cfdc8e95f07881a' and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']==digest(root/'scripts/build/phase2/gsound-build.sh')
 assert (l/'gsound-1.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert r['original_tests_registered']==[] and r['no_registered_tests_not_a_pass']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 options={o['name']:o['value'] for o in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text())};assert options['introspection'] and options['enable_vala'] and not options['gtk_doc']
 return r
