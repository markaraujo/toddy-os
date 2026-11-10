#!/bin/bash
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py geoclue
chroot /mnt/lfs groupadd -g 30 geoclue
chroot /mnt/lfs useradd -r -u 30 -g 30 -M -d /var/lib/geoclue -s /bin/false geoclue
python3 - <<'PY'
from pathlib import Path
import json
p=Path('/var/log/toddy/packages/geoclue_2.8.2-1+toddy1_amd64.json');r=json.loads(p.read_text());assert r['installed']
r['runtime_profile']={'service_account':{'name':'geoclue','uid':30,'gid':30,'home':'/var/lib/geoclue','shell':'/bin/false','password_assigned':False},'initialization':'Versioned full-root recipe after native package installation; fixed sysusers ID matches explicit locked account, no unrelated user replacement.','backend':True,'hardware_sources_omitted':['ModemManager 3G/CDMA/GPS','Avahi network NMEA'],'permission_scope':'No owner location/scan/submission permission granted by package installation; actual service policy/GNOME UI gate pending.'}
part=p.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(r,indent=2)+'\n');part.replace(p)
PY
