#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from schema_union_install import verify
failed=json.loads(Path('/var/log/toddy/build/b02-networkmanager-install.failed.json').read_text());assert failed['recipe_exit']==0 and failed['postcheck_exit']==1
r=json.loads(Path('/var/log/toddy/packages/networkmanager_1.58.1-1+toddy1_amd64.json').read_text());assert r['installed'];verify(r)
a=Path('/var/cache/toddy/packages/networkmanager_1.58.1-1+toddy1_amd64.deb')
with a.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['archive_sha256']=='07119693e9057d7b9a2a18c17361b5064d08d4a067624b4aead843e9031a02e4'
Path('/var/log/toddy/phase2/networkmanager-payload-verify-2.json').write_text(json.dumps({'scope':'Read-only recovery of own CLI distribution-version assertion; exact upstream package/SDK1.58.1 and source dist_version=ToddyOS retained; no install/source/compiler replay.','owned_payload_entries_verified':len(r['payload']),'archive_sha256':r['archive_sha256'],'payload_unchanged':True},indent=2)+'\n')
PY
