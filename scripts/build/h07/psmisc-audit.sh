#!/bin/bash
# Verify the installed package without reinstalling after version-stream error.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-psmisc.failed.json').read_text())
assert r['recipe_exit']==0 and r['postcheck_exit']==1
CHECK
[[ -z $(dpkg --root="$LFS" --verify psmisc) ]]
