#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import os
w=Path('/mnt/lfs/sources/phase2/work/libpwquality-1/stage');size=sum(p.stat().st_size for p in w.rglob('*') if p.is_file() and not p.is_symlink())
s=os.statvfs('/mnt/lfs');assert s.f_bavail*s.f_frsize>=16*1024**3+3*size+8*1024**2,'Retain target reserve through staging/archive/install'
PY
python3 - <<'PAM_SNAPSHOT'
from pathlib import Path
import json,hashlib
T=Path('/mnt/lfs');p=Path('/var/log/toddy/phase2/libpwquality-pam-before.json');assert not p.exists()
files=[x for x in (T/'etc/pam.d').rglob('*') if x.is_file() and not x.is_symlink()]
assert files and all('pam_pwquality.so' not in x.read_text() for x in files), 'Review existing active PAM use before exposing a newly installed module'
r={str(x.relative_to(T)):hashlib.sha256(x.read_bytes()).hexdigest() for x in files};p.write_text(json.dumps(r,indent=2)+'\n');p.chmod(0o600)
PAM_SNAPSHOT
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py libpwquality
