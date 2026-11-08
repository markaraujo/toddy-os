#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
chroot "$LFS" /usr/bin/python3 -B - < /opt/toddy-build/scripts/build/phase2/sassc-probe.py > /var/log/toddy/phase2/sassc-installed-consumer.json
python3 - <<'PYTHON'
from pathlib import Path
import json,subprocess
p=json.loads(Path('/var/log/toddy/packages/sassc_3.6.2-1+toddy1_amd64.json').read_text());assert p['installed']
subprocess.run(['chroot','/mnt/lfs','apt-get','check'],check=True)
PYTHON
