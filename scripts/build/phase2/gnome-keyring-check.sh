#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,shutil,subprocess,tempfile
prefix=['chroot','/mnt/lfs'];env={'PATH':'/usr/bin:/usr/sbin','LC_ALL':'C.UTF-8','HOME':'/root'}
assert subprocess.check_output(prefix+['dpkg-query','-W','-f=${Status} ${Version}','gnome-keyring'],text=True,env=env)=='install ok installed 50.0-1+toddy1'
assert not subprocess.check_output(prefix+['dpkg','--audit'],text=True,env=env).strip()
subprocess.run(prefix+['apt-get','check'],env=env,check=True)
probe=Path('/opt/toddy-build/scripts/build/phase2/gnome-keyring-probe.py').read_text()
r=subprocess.run(prefix+['python3','-c',probe,'/'],env=env,capture_output=True,text=True,timeout=20,check=True)
consumer=json.loads(r.stdout);assert consumer['production_test_hooks_disabled']
assert not any('pam_gnome_keyring.so' in p.read_text() for p in Path('/mnt/lfs/etc/pam.d').glob('*') if p.is_file()),'PAM login policy is a separate controlled native integration'
Path('/var/log/toddy/phase2/gnome-keyring-installed-consumer.json').write_text(json.dumps({'scope':'Installed production CLI/PAM loader/package audit only; actual native PAM/GNOME/GUI and shared schema cache integration pending','consumer':consumer,'PAM_policy_changed':False},indent=2)+'\n')
PY
