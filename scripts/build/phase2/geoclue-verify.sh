#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2')
from schema_union_install import verify
failed=json.loads(Path('/var/log/toddy/build/b02-geoclue-install.failed.json').read_text());assert failed['recipe_exit']==0 and failed['postcheck_exit']==1
r=json.loads(Path('/var/log/toddy/packages/geoclue_2.8.2-1+toddy1_amd64.json').read_text());assert r['installed'];verify(r)
a=Path('/var/cache/toddy/packages/geoclue_2.8.2-1+toddy1_amd64.deb')
with a.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['archive_sha256']=='7be463fcebf553d7a7bad9f7a68400ad3cf3adcc99509535f3affb4f4ac6c418'
assert r['runtime_profile']['service_account']['uid']==30
Path('/var/log/toddy/phase2/geoclue-payload-verify-2.json').write_text(json.dumps({'scope':'Read-only recovery of own GI property-access check, no install/account/native source replay.','owned_payload_entries_verified':len(r['payload']),'archive_sha256':r['archive_sha256'],'runtime_profile':r['runtime_profile'],'payload_unchanged':True},indent=2)+'\n')
PY
