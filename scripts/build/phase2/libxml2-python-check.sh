#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
chroot "$LFS" /usr/bin/python3 -B - < /opt/toddy-build/scripts/build/phase2/xml_python_probe.py > /var/log/toddy/phase2/libxml2-python-installed-consumer.json
python3 - <<'PY'
import json
from pathlib import Path
p=json.loads(Path('/var/log/toddy/packages/libxml2-python_2.15.3-1+toddy1_amd64.json').read_text())
assert p['installed']
PY
