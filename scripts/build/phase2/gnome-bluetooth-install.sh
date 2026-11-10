#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import os
w=Path('/mnt/lfs/sources/phase2/work/gnome-bluetooth-1/stage');size=sum(p.stat().st_size for p in w.rglob('*') if p.is_file() and not p.is_symlink())
s=os.statvfs('/mnt/lfs');assert s.f_bavail*s.f_frsize>=16*1024**3+3*size+8*1024**2,'Retain target reserve through staging/archive/install'
PY
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py gnome-bluetooth
