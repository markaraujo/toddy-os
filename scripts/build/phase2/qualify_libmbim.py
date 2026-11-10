"""Bind libmbim protocol tests, stage bytes and unchanged root-only defaults."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libmbim-1.34.0');w=Path('/mnt/lfs/sources/phase2/work/libmbim-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());locked=next(x for x in json.loads((root/'config/phase2/sources.lock.json').read_text())['components'] if x['name']=='libmbim')
 assert p['source_sha256']==locked['sha256'] and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']==digest(root/'scripts/build/phase2/libmbim-build.sh')
 assert (l/'libmbim-1.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert len(r['original_tests'])==9 and all(t['returncode']==0 and t['result']=='OK' for t in r['original_tests'])
 assert sum(t['stdout'].count('\nok ') for t in r['original_tests'])==131
 config=(w/'compile/config.h').read_text();assert '#undef MBIM_USERNAME_ENABLED' in config and '#undef MBIM_GROUPNAME_ENABLED' in config
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 return r
