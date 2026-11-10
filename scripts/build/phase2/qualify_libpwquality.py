"""Bind libpwquality's immutable build and explicitly absent original suite."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libpwquality-1.4.5');w=Path('/mnt/lfs/sources/phase2/work/libpwquality-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='6fcf18b75d305d99d04d2e42982ed5b787a081af2842220ed63287a2d6a10988' and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']==digest(root/'scripts/build/phase2/libpwquality-build.sh')
 assert (l/'libpwquality-1.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert r['original_test_suite_available'] is False and r['no_original_suite_not_a_pass']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 return r
