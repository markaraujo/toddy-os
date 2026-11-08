#!/bin/bash
# Original transaction installed successfully; reconcile without replaying it.
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'VERIFY'
import hashlib,json
from pathlib import Path
p=Path('/var/log/toddy/build/b02-wayland-install.failed.json')
d=json.loads(p.read_text());assert d['recipe_exit']==0 and d['postcheck_exit']==1
p=Path('/var/log/toddy/packages/wayland_1.26.0-1+toddy1_amd64.json');d=json.loads(p.read_text());assert d['installed'] is True
p=Path('/var/cache/toddy/packages/wayland_1.26.0-1+toddy1_amd64.deb')
assert hashlib.sha256(p.read_bytes()).hexdigest()==d['archive_sha256']=='0031e4f647de651dc3209c9692ca8294fb6c408b0cad439ccffa4e4d7ff85f48'
VERIFY
