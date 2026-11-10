#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import sys,os,json
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_cups import qualify
from native_scratch_staging import allocation,check_workspace
from cups_native import accounts
qualify(Path('/opt/toddy-build'))
stage=Path('/mnt/lfs/sources/phase2/work/cups-layout-1/stage')
space=os.statvfs('/mnt/lfs');assert space.f_bavail*space.f_frsize>=16*1024**3+2*allocation(stage)+8*1024**2
workspace=json.loads(Path('/var/log/toddy/phase2/native-output-scratch-1.json').read_text());assert workspace['state']=='complete';check_workspace(workspace)
assert not list(Path(workspace['source']).iterdir())
space=os.statvfs(workspace['source']);assert space.f_bavail*space.f_frsize>=512*1024**2+16*1024**2
accounts()
PY
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py cups
