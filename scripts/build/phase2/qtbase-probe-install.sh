#!/bin/bash
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
cd /opt/toddy-build
python3 - <<'VERIFY'
from pathlib import Path
import json,sys,shutil
sys.path.insert(0,'scripts/build/phase2')
from verify_stage import inspect_stage
from package_copyright import write_copyright
source=Path('/mnt/lfs/sources/phase2/work/qtbase-probe-1/stage')
before=inspect_stage(source)
assert 'usr/lib/libQt6Widgets.so.6.11.2' in before['entries']
destination=Path('/mnt/lfs/sources/stage/phase2-qtbase-probe')
assert not destination.exists(), 'Inspect existing stage before replay'
shutil.copytree(source,destination,symlinks=True)
assert inspect_stage(destination)==before
Path('/var/log/toddy/phase2/qtbase-probe-stage.json').write_text(json.dumps(before,indent=2)+'\n')
write_copyright(destination,'qtbase',['qtbase-everywhere-src-6.11.2.tar.xz'])
VERIFY
python3 scripts/build/stage_package.py qtbase 6.11.2-1+toddy1 \
    "$LFS/sources/stage/phase2-qtbase-probe" \
    --source qtbase-everywhere-src-6.11.2.tar.xz \
    --recipe scripts/build/phase2/qtbase-probe-install.sh \
    --depends 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), dbus (>= 1.16.2-1), openssl (>= 4.0.3-1), zlib (>= 1.3.2-1), zstd (>= 1.5.7-1), glib (>= 2.88.3-1), systemd (>= 261.2-1)' --install
