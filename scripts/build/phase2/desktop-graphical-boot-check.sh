#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess
T=Path('/mnt/lfs');L=Path('/var/log/toddy/phase2');r=json.loads((L/'desktop-graphical-boot-1.json').read_text());assert r['state']=='complete'
assert (T/'etc/systemd/system/default.target').readlink()==Path(r['after_default'])
assert (T/'etc/systemd/system/display-manager.service').readlink()==Path(r['display_manager'])
for name in ['default.target','display-manager.service']:
 p=T/'etc/systemd/system'/name;s=p.lstat();assert s.st_uid==s.st_gid==0
assert subprocess.check_output(['chroot',str(T),'systemctl','--root=/','get-default'],text=True).strip()=='graphical.target'
assert subprocess.check_output(['chroot',str(T),'systemctl','--root=/','is-enabled','gdm.service'],text=True).strip()=='enabled'
assert (T/'etc/systemd/system/systemd-networkd-wait-online.service').readlink()==Path('/dev/null')
assert not (T/'etc/systemd/system/network-online.target.wants/NetworkManager-wait-online.service').exists()
(L/'desktop-graphical-boot-check-1.json').write_text(json.dumps({'scope':'Native generated boot links/default/offline-wait preservation only; actual power-on GNOME acceptance pending','default_target':'graphical.target','display_manager':'gdm.service','native_boot_verified':False},indent=2)+'\n')
PY
