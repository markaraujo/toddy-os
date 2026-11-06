#!/bin/bash
# Recheck generated code with the headers required by the generated interface.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-gperf.failed.json').read_text())
assert r['recipe_exit']==0 and r['postcheck_exit']==1
CHECK
[[ -z $(dpkg --root="$LFS" --verify gperf) ]]
