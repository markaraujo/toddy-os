#!/bin/bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import json
r=json.loads(Path('/var/log/toddy/build/b02-gdm-install.failed.json').read_text());assert r['recipe_exit']==127 and r['postcheck_exit'] is None
p=Path('/var/log/toddy/packages/gdm_50.2-1+toddy1_amd64.json');r=json.loads(p.read_text());assert r['installed'] and r['archive_sha256']=='520670ee20a2f70cd4b66411e878c0190ca2d3522392e7f76a02aa22cc512adb'
assert not Path('/var/log/toddy/phase2/gdm-group-initialization.json').exists()
PY
python3 /opt/toddy-build/scripts/build/phase2/initialize_gdm_group.py
