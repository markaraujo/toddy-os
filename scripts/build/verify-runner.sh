#!/bin/bash
set -euo pipefail
cd /opt/toddy-build/scripts/build
python3 run_step.py h03-success probe-success.sh probe-postcheck.sh
if python3 run_step.py h03-failure probe-failure.sh probe-postcheck.sh; then exit 1; fi
if python3 run_step.py h03-postfailure probe-success.sh probe-failure.sh; then exit 1; fi
python3 - <<'PY'
import json
from pathlib import Path
p=Path('/var/log/toddy/build')
assert json.loads((p/'h03-success.success.json').read_text())['postcheck_exit']==0
assert json.loads((p/'h03-failure.failed.json').read_text())['recipe_exit']==42
assert json.loads((p/'h03-postfailure.failed.json').read_text())['postcheck_exit']==42
for step in ['h03-failure','h03-postfailure']:
 assert not (p/f'{step}.success.json').exists()
assert '/var/toddy-runner-probe' in json.loads((p/'h03-success.manifest.json').read_text())
print('PASS: exit tracking, failed postconditions, no false success markers and content manifests')
PY
rm /mnt/lfs/var/toddy-runner-probe
su - lfs -c 'source /home/lfs/.bashrc; env | sort'
