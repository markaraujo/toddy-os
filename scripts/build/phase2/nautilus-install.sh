#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import shutil
stage=Path('/mnt/lfs/sources/phase2/work/nautilus-1/stage')
size=sum(p.stat().st_size for p in stage.rglob('*') if p.is_file() and not p.is_symlink())
assert shutil.disk_usage('/mnt/lfs').free>=16*1024**3+3*size+16*1024**2
PY
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py nautilus
