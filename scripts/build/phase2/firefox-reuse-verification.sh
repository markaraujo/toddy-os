#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'INNER'
from pathlib import Path
import json
L=Path('/var/log/toddy');old=json.loads((L/'build/b02-firefox-verify-2.failed.json').read_text())
assert old['recipe_exit']==0 and old['postcheck_exit']==1
r=json.loads((L/'phase2/firefox-package-verify-2.json').read_text());assert r['state']=='verified-existing-package'
p=json.loads((L/'packages/firefox_153.7.0esr-1+toddy1_amd64.json').read_text());assert p['installed'] and p['archive_sha256']==r['archive_sha256']
print('Prior read-only archive/stage verification reused; only failed runtime postcondition changes context')
INNER
