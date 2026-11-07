#!/bin/bash
# Native source-built Node transaction, after the isolated job's real exit receipt.
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
cd /opt/toddy-build
python3 - <<'VERIFY'
import json,sys,shutil
from pathlib import Path
sys.path.insert(0,'scripts/build/phase2')
from verify_stage import inspect_stage
status=json.loads(Path('status.json').read_text())
assert status['owner_review']['phase_2_approved'] is True
assert next(r for r in status['milestones'] if r['id']=='B01')['status']=='in_progress'
assert Path('/var/log/toddy/phase2/node-bootstrap-1.exit').read_text().strip()=='0'
work=Path('/mnt/lfs/sources/phase2/work/node-bootstrap-1')
assert (work/'stage/usr/bin/node').is_file()
before=inspect_stage(work/'stage')
destination=Path('/mnt/lfs/sources/stage/phase2-node-bootstrap')
assert not destination.exists(), 'Inspect prior transaction before replay'
shutil.copytree(work/'stage',destination,symlinks=True)
assert inspect_stage(destination)==before
Path('/var/log/toddy/phase2/node-bootstrap-stage.json').write_text(json.dumps(before,indent=2)+'\n')
VERIFY
install -Dm644 "$LFS/sources/phase2/inputs/node-v24.19.0/LICENSE" \
    "$LFS/sources/stage/phase2-node-bootstrap/usr/share/doc/nodejs/copyright"
python3 scripts/build/stage_package.py nodejs 24.19.0-1+toddy1 \
    "$LFS/sources/stage/phase2-node-bootstrap" --source node-v24.19.0.tar.xz \
    --recipe scripts/build/phase2/node-install.sh \
    --depends 'glibc (>= 2.44-1), gcc (>= 16.2.0-1)' --install
