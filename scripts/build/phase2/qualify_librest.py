"""Verify original local librest evidence and unchanged compiler/stage bytes."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/librest-0.10.2');w=Path('/mnt/lfs/sources/phase2/work/librest-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='7b6cb912bb3a22cfa7dcf005925dcb62883024db0c09099486e7d6851185c9b8' and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']
 assert (l/'librest-1.exit').read_text().strip()=='0'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert len(r['tests'])==7 and all(t['returncode']==0 and t['result']=='OK' for t in r['tests'])
 assert r['flickr_local_case'] and r['unexecuted_external_cases']==['/flickr/flickr','/lastm/lastfm']
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 options={o['name']:o['value'] for o in json.loads((w/'compile/meson-info/intro-buildoptions.json').read_text())}
 assert options['vapi'] and options['introspection'] and not options['soup2'] and not options['examples'] and not options['gtk_doc']
 return r
