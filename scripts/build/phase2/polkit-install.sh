#!/bin/bash
set -euo pipefail
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py polkit
# Native archive/payload/install succeeded first. These declared account effects
# are part of this same full-root transaction, not imported maintainer scripts.
chroot /mnt/lfs groupadd -g 27 polkitd
chroot /mnt/lfs useradd -r -u 27 -g 27 -M -d /etc/polkit-1 -s /bin/false polkitd
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('/var/log/toddy/packages/polkit_127-1+toddy1_amd64.json');r=json.loads(p.read_text());assert r['installed']
r['runtime_profile']={'service_account':{'name':'polkitd','uid':27,'gid':27,'home':'/etc/polkit-1','shell':'/bin/false','password_assigned':False},'account_initialization':'Versioned root recipe after verified native archive installation; existing unrelated accounts are never replaced','helper_transport':'Qualified upstream standard SUID fallback; optional helper.socket not enabled/unqualified','native_qualification_receipt_sha256':hashlib.sha256(Path('/var/log/toddy/phase2/polkit-standard-native-acceptance-1.json').read_bytes()).hexdigest()}
part=p.with_suffix('.part');assert not part.exists();part.write_text(json.dumps(r,indent=2)+'\n');part.replace(p)
PY
