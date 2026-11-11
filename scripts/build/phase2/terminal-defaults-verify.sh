#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from schema_union_install import verify
failed=json.loads(Path('/var/log/toddy/build/b02-terminal-defaults-install.failed.json').read_text())
assert failed['recipe_exit']==0 and failed['postcheck_exit']==1
assert "AssertionError: ('opt-out', 1" in Path('/var/log/toddy/build/b02-terminal-defaults-install.log').read_text()
record=json.loads(Path('/var/log/toddy/packages/toddy-terminal_0.2.0-1+toddy1_all.json').read_text())
assert record['installed'];verify(record)
archive=Path('/var/cache/toddy/packages/toddy-terminal_0.2.0-1+toddy1_all.deb')
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==record['archive_sha256']=='2cdbca318a0b1f623eeb3ce5da84d0b95cda5ec900e425caf14a6ad94247841f'
Path('/var/log/toddy/phase2/terminal-defaults-payload-verify-2.json').write_text(json.dumps({'scope':'Verify-only recovery of prompt expectation quoting; original installed module/archive/payload unchanged, no reinstall. Corrected behavioral postchecks remain required.','archive_sha256':record['archive_sha256'],'payload_entries':len(record['payload']),'payload_unchanged':True},indent=2)+'\n')
PY
