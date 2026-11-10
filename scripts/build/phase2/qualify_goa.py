"""Bind GOA's immutable build, metadata-only recovery and provider availability."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gnome-online-accounts-3.58.1');w=Path('/mnt/lfs/sources/phase2/work/gnome-online-accounts-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());assert p['source_sha256']=='9ec1900cc51409c2067c07c828c10be06fe3bf68d2999bb72d7d5ed325ed9bbc' and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256']=='071649dab8c9f5c61f84598b1e98f70f47d9c289884d394e6bebfb3a6c085363'
 assert (l/'gnome-online-accounts-1.exit').read_text().strip()=='1' and (l/'gnome-online-accounts-collect-2.exit').read_text().strip()=='0'
 assert json.loads((l/'gnome-online-accounts-collect-2.job.json').read_text())['command'][-1]==(root/'scripts/build/phase2/gnome_online_accounts_collect_stage.py').read_text()
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0
 assert r['original_tests_registered']==[] and r['no_registered_tests_not_a_pass']
 assert r['consumer']['version']=='goa-daemon 3.58.1\n'
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 for base,rows in json.loads((w/'before-collect-2.json').read_text()).items():
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink()};assert actual==rows
 config=(w/'compile/config.h').read_text()
 for option in ['GOA_GOOGLE_ENABLED','GOA_MS_GRAPH_ENABLED','GOA_KERBEROS_ENABLED','GOA_FEDORA_ENABLED']:assert '#undef '+option in config
 for option in ['GOA_GOOGLE_CLIENT_ID','GOA_GOOGLE_CLIENT_SECRET','GOA_MS_GRAPH_CLIENT_ID']:assert '#define '+option+' ""' in config
 assert '#define GOA_BACKEND_ENABLED' in config.splitlines()
 return r
