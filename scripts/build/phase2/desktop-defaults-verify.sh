#!/bin/bash
# Verify-only recovery; native package transaction already completed.
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PYCODE'
from pathlib import Path
import json,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from schema_union_install import verify
f=json.loads(Path('/var/log/toddy/build/b02-desktop-defaults-install.failed.json').read_text())
assert f['recipe_exit']==0 and f['postcheck_exit']==1
r=json.loads(Path('/var/log/toddy/packages/toddy-desktop-defaults_0.2.0-1+toddy1_all.json').read_text());assert r['installed']
verify(r)
PYCODE
