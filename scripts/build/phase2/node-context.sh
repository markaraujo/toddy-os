#!/bin/bash
# Reconcile the committed Node transaction; never replay its package installation.
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'RECONCILE'
from pathlib import Path
import json,hashlib
prefix=Path('/var/log/toddy/build/b01-node-bootstrap-install')
record=json.loads(prefix.with_suffix('.failed.json').read_text())
assert record['recipe_exit']==0 and record['postcheck_exit']==1
log=prefix.with_suffix('.log').read_text()
assert "actual: 'node'" in log and "expected: '/usr/bin/node'" in log
assert not prefix.with_suffix('.running.json').exists()
package=Path('/var/log/toddy/packages/nodejs_24.19.0-1+toddy1_amd64.json')
data=json.loads(package.read_text());assert data['installed'] is True
archive=Path('/var/cache/toddy/packages/nodejs_24.19.0-1+toddy1_amd64.deb')
with archive.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==data['archive_sha256']
RECONCILE
bash /opt/toddy-build/scripts/build/mount-kernfs.sh
mountpoint -q "$LFS/proc"
