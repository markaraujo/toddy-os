#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,sys
root=Path('/opt/toddy-build');T=Path('/mnt/lfs');l=Path('/var/log/toddy')
r=json.loads((l/'build/b02-gsound-dependency-install-2.failed.json').read_text());assert r['recipe_exit']==0 and r['postcheck_exit']==1 and r['changed_paths']==3
assert 'DSO missing from command line' in (l/'build/b02-gsound-dependency-install-2.log').read_text()
assert subprocess.check_output(['chroot',str(T),'dpkg-query','-W','-f=${Status} ${Version}','gsound'],text=True)=='install ok installed 1.0.3-1+toddy2'
sys.path.insert(0,str(root/'scripts/build/phase2'));from qualify_gsound import qualify,digest
r=qualify(root)
for relative,sha in r['stage_sha256'].items():assert digest(T/relative)==sha
assert digest(Path('/var/cache/toddy/packages/gsound_1.0.3-1+toddy1_amd64.deb'))=='9cc4d3f270e96549440e6bd27c72d07700d583ec1adbbbd1ac3636d8d25fc2ee'
assert digest(Path('/var/cache/toddy/packages/gsound_1.0.3-1+toddy2_amd64.deb'))=='0803a83e6a19ea9fe1ae04759339fccee2b5322113670f295e816eb6950e6e30'
print('GSound verify-only: explicit own GObject/GIO linker flags, no package transaction')
PY
