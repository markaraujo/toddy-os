#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from qualify_mitkrb import qualify
from native_scratch_staging import prepare
qualify(Path('/opt/toddy-build'))
prepare('mitkrb')
PY
python3 /opt/toddy-build/scripts/build/phase2/install_verified_stage.py mitkrb
