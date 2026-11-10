"""Bind actual Shell compile/stage and one own probe-only recovery."""
from pathlib import Path
import hashlib,json

def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def qualify(root):
 s=Path('/mnt/lfs/sources/phase2/inputs/gnome-shell-50.4');w=Path('/mnt/lfs/sources/phase2/work/gnome-shell-1');l=Path('/var/log/toddy/phase2')
 assert (s/'toddy-build.sh').read_bytes()==(root/'scripts/build/phase2/gnome-shell-build.sh').read_bytes()
 prep=json.loads((s/'toddy-prepared.json').read_text());assert prep['source_sha256']=='c531939539db316a41aef23670370abd1330d3254f84bcb0f9f4dae5d6e362cf'
 assert len(prep['source_patches'])==1 and prep['source_patches'][0]['after_sha256']==digest(s/'src/calendar-server/gnome-shell-calendar-server.c')
 proof=json.loads((w/'stage-results.json').read_text())
 if (l/'gnome-shell-probe-2.exit').exists():
  assert (l/'gnome-shell-1.exit').read_text().strip()=='1'
  assert 'range_check(bad)' in (l/'gnome-shell-1.log').read_text()
  assert digest(s/'toddy-probe.py')=='be2214c14c4968c3dc8078cc6e3b48d91ee96256cb718c87d1864a1b286ba33e'
  assert (l/'gnome-shell-probe-2.exit').read_text().strip()=='0'
  code=(root/'scripts/build/phase2/gnome_shell_probe_resume.py').read_text()+'\nmain('+repr((root/'scripts/build/phase2/gnome-shell-probe.py').read_text())+')\n'
  assert json.loads((l/'gnome-shell-probe-2.job.json').read_text())['command'][-3:]==['python3','-c',code]
  assert (w/'probe-2/probe.py').read_bytes()==(root/'scripts/build/phase2/gnome-shell-probe.py').read_bytes()
  assert proof['probe_only_recovery']['compile_and_stage_unchanged']
 else:
  assert (l/'gnome-shell-1.exit').read_text().strip()=='0'
  assert (s/'toddy-probe.py').read_bytes()==(root/'scripts/build/phase2/gnome-shell-probe.py').read_bytes()
 assert proof['compile_exit']==proof['stage_exit']==0 and proof['original_tests']==[] and proof['original_suite_pending']
 assert json.loads((w/'original-registered-tests.json').read_text())==[]
 assert len(proof['artifacts'])==128 and len(proof['stage_sha256'])==149
 for base,key in [('compile','artifacts'),('stage','stage_sha256')]:
  for name,sha in proof[key].items():assert digest(w/base/name)==sha
 c=proof['consumer'];assert c['GI_type']=='StWidget' and c['params']['cycles']==2
 assert c['params']['unknown_refused'] and c['params']['recovery']
 assert c['favorite_apps_cycles']==2 and c['wrong_type_refused'] and not c['preferences_changed']
 assert (w/'shell-version.log').read_text().strip()=='GNOME Shell 50.4'
 return proof
