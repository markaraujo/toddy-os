#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import sys,json,subprocess
root=Path('/opt/toddy-build');T=Path('/mnt/lfs');log=Path('/var/log/toddy')
r=json.loads((log/'build/b02-libqmi-canonical-install-2.failed.json').read_text());assert r['recipe_exit']==0 and r['postcheck_exit']==1 and r['changed_paths']==93
assert "object has no attribute 'Message'" in (log/'build/b02-libqmi-canonical-install-2.log').read_text()
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','libqmi'],text=True)=='install ok installed 1.38.0-1+toddy1'
sys.path.insert(0,str(root/'scripts/build/phase2'));from qualify_libqmi import qualify,digest
proof=qualify(root)
for relative,sha in proof['stage_sha256'].items():assert digest(T/relative)==sha
record=json.loads((log/'packages/libqmi_1.38.0-1+toddy1_amd64.json').read_text());assert record['installed']
assert digest(Path('/var/cache/toddy/packages/libqmi_1.38.0-1+toddy1_amd64.deb'))==record['archive_sha256']
print('Verify-only with actual installed GIR ClientDms; no package transaction')
PY
