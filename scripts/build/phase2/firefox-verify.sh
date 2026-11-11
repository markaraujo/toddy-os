#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'INNER'
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/opt/toddy-build/scripts/build');from stage_package import payload
L=Path('/var/log/toddy');old=json.loads((L/'build/b02-firefox-install.failed.json').read_text());assert old['recipe_exit']==1 and old['postcheck_exit'] is None
r=json.loads((L/'packages/firefox_153.7.0esr-1+toddy1_amd64.json').read_text());assert r['installed']
archive=Path('/var/cache/toddy/packages/firefox_153.7.0esr-1+toddy1_amd64.deb')
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['archive_sha256']
actual=payload(Path('/mnt/lfs/sources/stage/phase2-firefox-security-1'))
controls={n for n in actual if n=='/DEBIAN' or n.startswith('/DEBIAN/')}
assert controls=={'/DEBIAN','/DEBIAN/control'}
assert {n:v for n,v in actual.items() if n not in controls}==r['payload']
p=L/'phase2/firefox-package-verify-2.json';assert not p.exists()
p.write_text(json.dumps({'scope':'Read-only verification of completed native install after own packaging-control comparison error; original recipe failure retained, no package reinstall','state':'verified-existing-package','archive_sha256':r['archive_sha256'],'payload_entries':len(r['payload']),'excluded_native_control_paths':sorted(controls)},indent=2)+'\n')
INNER
