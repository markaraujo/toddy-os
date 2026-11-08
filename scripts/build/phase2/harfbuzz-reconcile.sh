#!/bin/bash
# Original transaction installed successfully; reconcile without replaying it.
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'VERIFY'
import hashlib,json
from pathlib import Path
p=Path('/var/log/toddy/build/b02-harfbuzz-install.failed.json')
d=json.loads(p.read_text());assert d['recipe_exit']==0 and d['postcheck_exit']==1
p=Path('/var/log/toddy/packages/harfbuzz_14.3.1-1+toddy1_amd64.json');d=json.loads(p.read_text());assert d['installed'] is True
p=Path('/var/cache/toddy/packages/harfbuzz_14.3.1-1+toddy1_amd64.deb')
assert hashlib.sha256(p.read_bytes()).hexdigest()==d['archive_sha256']=='21428e45e4d84ee41760caa25b3e67a671c98a8f31ecd105a3c81b72b79cd66b'
VERIFY
