#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import sys,json,subprocess
root=Path('/opt/toddy-build');T=Path('/mnt/lfs');log=Path('/var/log/toddy')
r=json.loads((log/'build/b02-modemmanager-verify-2.failed.json').read_text());assert r['recipe_exit']==0 and r['postcheck_exit']==1 and r['changed_paths']==0
assert 'line 28' in (log/'build/b02-modemmanager-verify-2.log').read_text() and 'AssertionError' in (log/'build/b02-modemmanager-verify-2.log').read_text()
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','modemmanager'],text=True)=='install ok installed 1.24.2-1+toddy1'
sys.path.insert(0,str(root/'scripts/build/phase2'));from qualify_modemmanager import qualify,digest
proof=qualify(root)
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
record=json.loads((log/'packages/modemmanager_1.24.2-1+toddy1_amd64.json').read_text());assert record['installed']
assert digest(Path('/var/cache/toddy/packages/modemmanager_1.24.2-1+toddy1_amd64.deb'))==record['archive_sha256']=='99f7fb0f17a67a7ec0829c696d50485e5a7adceae2dcef80133718283c9b5572'
print('Verify-only with source-backed absent-system-bus CLI refusal; no package transaction')
PY
