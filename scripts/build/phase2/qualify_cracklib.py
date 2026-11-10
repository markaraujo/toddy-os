"""Verify exact Cracklib tests, dictionary provenance, and preserved build bytes."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/cracklib-2.10.3');w=Path('/mnt/lfs/sources/phase2/work/cracklib-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='1d1b83676b5673051b9373e1ca0db81c1fa88faf9a195a3c1af984fd9c250d66' and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']=='1a3a48b23446069e0b34914fe18c011d621225dee1da18e8c69860c8e05114b0'
 assert (l/'cracklib-1.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 for line in ['# TOTAL: 2','# PASS:  2','# SKIP:  0','# FAIL:  0','# ERROR: 0']:assert line in r['original_test_suite']
 row=r['dictionary_source'];assert row==p['extra_source'] and row['sha256']=='b3d1e0e0ae9bc7ffed65c0042d7c68bdb903368aa6b918f94572453c6ea874dc'
 assert digest(s/'toddy-words.xz')==row['sha256'] and digest(w/'original-words')==row['expanded_sha256']=='72850d6a542578ccedc74088bbe31ce2a872bf447ea61d05661879b8430c5f6f'
 assert digest(s/'README-WORDS')==row['license_provenance_sha256']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 return r
