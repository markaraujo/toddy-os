#!/bin/bash
# Reconcile the committed scanner package; fix its private-module check, not install.
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'VERIFY'
from pathlib import Path
import hashlib,json
p=Path('/var/log/toddy/build/b01-introspection-bootstrap-install.failed.json')
d=json.loads(p.read_text());assert d['recipe_exit']==0 and d['postcheck_exit']==1
log=Path('/var/log/toddy/build/b01-introspection-bootstrap-install.log').read_text()
assert "ModuleNotFoundError: No module named 'giscanner'" in log
p=Path('/var/log/toddy/packages/gobject-introspection_1.86.0-1+toddy1_amd64.json')
d=json.loads(p.read_text());assert d['installed'] is True
p=Path('/var/cache/toddy/packages/gobject-introspection_1.86.0-1+toddy1_amd64.deb')
with p.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==d['archive_sha256']
VERIFY
