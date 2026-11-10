#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/target.sh
guard_target
python3 - <<'PY'
from pathlib import Path
import json,subprocess,sys,os
root=Path('/opt/toddy-build');T=Path('/mnt/lfs');log=Path('/var/log/toddy')
sys.path.insert(0,str(root/'scripts/build/phase2'))
from qualify_libqmi import qualify,digest
from native_scratch_staging import BASE,bind_stage,check_workspace
proof=qualify(root);failed=json.loads((log/'build/b02-libqmi-install.failed.json').read_text())
assert failed['recipe_exit']==1 and failed['postcheck_exit'] is None and failed['changed_paths']==0
assert 'Staging root must be a real directory under target sources/stage' in (log/'build/b02-libqmi-install.log').read_text()
archive=Path('/var/cache/toddy/packages/libqmi_1.38.0-1+toddy1_amd64.deb');assert not archive.exists()
assert not (log/'packages/libqmi_1.38.0-1+toddy1_amd64.json').exists()
state=subprocess.run(['chroot',str(T),'dpkg-query','-W','-f=${Status}','libqmi'],capture_output=True,text=True);assert state.returncode==1
r=json.loads((log/'phase2/libqmi-native-scratch-stage-1.json').read_text());assert r['state']=='prepared'
capacity=os.statvfs(T);assert capacity.f_bavail*capacity.f_frsize>=r['target_required_bytes']
physical=BASE/'toddy-editor-workers/native-transactions-1/libqmi-promotion-1';assert r['destination']==str(physical) and not (physical/'DEBIAN').exists()
for relative,sha in proof['stage_sha256'].items():assert digest(physical/relative)==sha
extras={str(p.relative_to(physical)) for p in physical.rglob('*') if p.is_file() and not p.is_symlink()}-set(proof['stage_sha256'])
assert extras and all(x.startswith('usr/share/doc/libqmi/') for x in extras)
workspace=json.loads((log/'phase2/native-output-scratch-1.json').read_text());assert workspace['state']=='complete';check_workspace(workspace)
stage=bind_stage('libqmi',physical)
subprocess.run(['python3',str(root/'scripts/build/stage_package.py'),'libqmi','1.38.0-1+toddy1',str(stage),
 '--source','libqmi-1.38.0.tar.gz','--recipe','scripts/build/phase2/libqmi-canonical-install.sh',
 '--depends','glibc (>= 2.44-1+toddy1), glib (= 2.88.3-1+toddy2), libmbim (= 1.34.0-1+toddy1), libgudev (= 238-1+toddy1)','--install'],cwd=root,check=True)
PY
