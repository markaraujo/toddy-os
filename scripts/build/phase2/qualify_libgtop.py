"""Bind the direct local API, original bytes and explicit staged-mode correction."""
from pathlib import Path
import hashlib,json,stat

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/libgtop-2.41.3');w=Path('/mnt/lfs/sources/phase2/work/libgtop-1');l=Path('/var/log/toddy/phase2')
 p=json.loads((s/'toddy-prepared.json').read_text());locked=next(x for x in json.loads((root/'config/phase2/sources.lock.json').read_text())['components'] if x['name']=='libgtop')
 assert p['source_sha256']==locked['sha256'] and not p['source_patches']
 assert digest(s/'toddy-build.sh')==p['recipe_sha256'] and digest(s/'toddy-probe.c')==p['probe_sha256']
 canonical=(root/'scripts/build/phase2/libgtop-build.sh').read_text();probe=(root/'scripts/build/phase2/libgtop-probe.c').read_text()
 if (l/'libgtop-mode-3.exit').exists():
  assert (l/'libgtop-1.exit').read_text().strip()==(l/'libgtop-collect-2.exit').read_text().strip()=='1'
  assert (l/'libgtop-mode-3.exit').read_text().strip()=='0'
  old=(s/'toddy-build-scratch.sh').read_text()
  a=canonical.index('# Keep the upstream chown/chmod hook grouped:');b=canonical.index('make DESTDIR=/stage install',a)
  assert canonical[:a]+canonical[b:]==old
  original=(s/'toddy-build.sh').read_text()
  assert original.replace('>=16*1024**3','>=512*1024**2').replace('export PYTHONDONTWRITEBYTECODE=1','[[ $(stat -c %d /build) != $(stat -c %d /usr) ]]\nexport PYTHONDONTWRITEBYTECODE=1')==old
  assert (s/'toddy-probe.c').read_text().replace('#include <glibtop/init.h>','#include <glibtop/open.h>')==probe
  command=(root/'scripts/build/phase2/libgtop_collect.py').read_text()+'\nmain('+repr(old)+','+repr(probe)+')\n'
  assert json.loads((l/'libgtop-collect-2.job.json').read_text())['command'][-1]==command
  command=(root/'scripts/build/phase2/libgtop_stage_mode.py').read_text()+'\nmain('+repr(canonical)+')\n'
  assert json.loads((l/'libgtop-mode-3.job.json').read_text())['command'][-1]==command
  correction=json.loads((w/'stage-helper-mode-correction-3.json').read_text());assert correction['state']=='complete' and correction['mode_before']=='0o4755' and correction['mode_after']=='0o755'
 else:
  assert (l/'libgtop-1.exit').read_text().strip()=='0'
  assert (s/'toddy-build-scratch.sh').read_text()==canonical and (s/'toddy-probe.c').read_text()==probe
 preparation=json.loads((l/'libgtop-shared-scratch-1.json').read_text());assert preparation['state']=='mounted'
 assert digest(s/'toddy-build-scratch.sh')==preparation['scratch_recipe_sha256'] and p['recipe_sha256']==preparation['original_recipe_sha256']
 assert json.loads((l/'libgtop-1.job.json').read_text())['command'][-1]=='/src/toddy-build-scratch.sh'
 r=json.loads((w/'stage-results.json').read_text());assert r['compile_exit']==r['stage_exit']==0 and not r['original_test_suite_available']
 assert r['consumer']=='Libgtop direct local memory/uptime/own-process/missing-PID refusal/two recoveries; no server or elevated identity\n' and r['version']=='2.41.3'
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  actual={str(p.relative_to(w/base)):digest(p) for p in (w/base).rglob('*') if p.is_file() and not p.is_symlink() and (key!='artifacts' or p.open('rb').read(4)==b'\x7fELF')};assert actual and actual==r[key]
 if (l/'libgtop-mode-3.exit').exists():
  before=json.loads((w/'before-collect-2.json').read_text());assert r['artifacts']==before['artifacts'] and r['stage_sha256']==before['stage_sha256']
 for entry in (w/'stage').rglob('*'):assert not entry.lstat().st_mode&(stat.S_ISUID|stat.S_ISGID)
 assert (w/'stage/usr/libexec/libgtop_server2').stat().st_mode&0o7777==0o755
 return r
