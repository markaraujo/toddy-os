#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,sys,subprocess
l=Path('/var/log/toddy/build');r=json.loads((l/'b02-gnome-online-accounts-install.failed.json').read_text());assert r['recipe_exit']==0 and r['postcheck_exit']==1 and r['changed_paths']==135
assert "AttributeError: 'AccountSkeleton' object has no attribute 'set_identity'" in (l/'b02-gnome-online-accounts-install.log').read_text()
assert subprocess.check_output(['chroot','/mnt/lfs','dpkg-query','-W','-f=${Status} ${Version}','gnome-online-accounts'],text=True)=='install ok installed 3.58.1-1+toddy1'
sys.path.insert(0,'/opt/toddy-build/scripts/build/phase2');from qualify_goa import qualify,digest
r=qualify(Path('/opt/toddy-build'))
for name,sha in r['stage_sha256'].items():assert digest(Path('/mnt/lfs')/name)==sha
print('Verify-only after own GI interface-property probe correction; no package transaction')
PY
