#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
cd /opt/toddy-build
python3 - <<'VERIFY'
from pathlib import Path
import json,sys,shutil
sys.path.insert(0,'scripts/build/phase2')
from verify_stage import inspect_stage
source=Path('/mnt/lfs/sources/phase2/work/pygobject-bootstrap-1/stage')
before=inspect_stage(source)
assert 'usr/lib/python3.14/site-packages/gi/__init__.py' in before['entries']
destination=Path('/mnt/lfs/sources/stage/phase2-pygobject-bootstrap')
assert not destination.exists(), 'Inspect existing stage before replay'
shutil.copytree(source,destination,symlinks=True)
assert inspect_stage(destination)==before
Path('/var/log/toddy/phase2/pygobject-bootstrap-stage.json').write_text(json.dumps(before,indent=2)+'\n')
VERIFY
stage=$LFS/sources/stage/phase2-pygobject-bootstrap
install -Dm644 "$LFS/sources/phase2/inputs/pygobject-3.56.3/COPYING" "$stage/usr/share/doc/pygobject/copyright"
python3 scripts/build/stage_package.py pygobject 3.56.3-1+toddy1 "$stage" \
    --source pygobject-3.56.3.tar.gz --recipe scripts/build/phase2/pygobject-install.sh \
    --depends 'glib (>= 2.88.3-1+toddy2), python (>= 3.14.10-1), libffi (>= 3.8.0-1)' --install
