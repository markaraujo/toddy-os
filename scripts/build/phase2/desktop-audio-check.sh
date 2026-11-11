#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,subprocess
T=Path('/mnt/lfs');r=json.loads(Path('/var/log/toddy/phase2/desktop-audio-policy.json').read_text())
for suffix,unit in r['links'].items():
 p=T/'etc/systemd/user'/suffix;assert p.is_symlink() and p.readlink()==Path('/usr/lib/systemd/user/'+unit)
for name,provider in r['providers'].items():
 record=json.loads(Path('/var/log/toddy/packages',name+'_'+provider['version']+'_amd64.json').read_text())
 for path,row in record['payload'].items():
  if path.startswith('/usr/lib/systemd/user/') and 'sha256' in row:assert hashlib.sha256((T/path.lstrip('/')).read_bytes()).hexdigest()==row['sha256']
rows=[]
for unit in ['pipewire.service','pipewire.socket','pipewire-pulse.service','pipewire-pulse.socket','wireplumber.service']:
 p=subprocess.run(['chroot',str(T),'systemctl','--root=/','--global','is-enabled',unit],capture_output=True,text=True)
 assert p.returncode==0 and p.stdout.strip()=='enabled',(unit,p.stdout,p.stderr)
 rows.append({'unit':unit,'exit':p.returncode,'state':p.stdout.strip()})
subprocess.run(['chroot',str(T),'apt-get','check'],check=True)
assert not subprocess.check_output(['chroot',str(T),'dpkg','--audit'],text=True).strip()
Path('/var/log/toddy/phase2/desktop-audio-policy-check.json').write_text(json.dumps({'scope':'Native systemd global-user enabled state, exact unit bytes and owned links. No live audio/physical hardware acceptance.','units':rows},indent=2)+'\n')
PY
