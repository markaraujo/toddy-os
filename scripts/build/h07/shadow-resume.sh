#!/bin/bash
# Diagnose/retry only account postconditions; the native package already installed.
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Version}' shadow) == '4.20.2-1' ]]
python3 - <<'PY'
import json
from pathlib import Path
record=json.loads(Path('/var/log/toddy/build/h07-shadow.failed.json').read_text())
assert record['recipe_exit']==0 and record['postcheck_exit']!=0
PY
dpkg --root="$LFS" --verify shadow
