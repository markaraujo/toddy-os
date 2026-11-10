#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import sys,json
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_modemmanager import qualify
from native_scratch_staging import prepare
qualify(Path('/opt/toddy-build'));print(json.dumps(prepare('modemmanager')))
PY
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py modemmanager
