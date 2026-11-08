#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
{
    cat <<'PY'
import sys,tempfile
_fixture_directory=tempfile.TemporaryDirectory(prefix='toddy-itstool-installed-')
sys.argv=['itstool-native-consumer',_fixture_directory.name+'/consumer']
PY
    cat /opt/toddy-build/scripts/build/phase2/itstool-probe.py
} | chroot "$LFS" /usr/bin/python3 -B - > /var/log/toddy/phase2/itstool-installed-consumer.json
python3 - <<'PY'
import json
from pathlib import Path
p=json.loads(Path('/var/log/toddy/packages/itstool_2.0.7-1+toddy1_amd64.json').read_text())
assert p['installed']
PY
