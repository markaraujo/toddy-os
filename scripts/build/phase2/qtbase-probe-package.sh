#!/bin/bash
# Resume verified preparation only: the earlier step never entered native Dpkg.
set -euo pipefail
source /opt/toddy-build/scripts/build/h06/common.sh
cd /opt/toddy-build
python3 - <<'VERIFY'
from pathlib import Path
import json,sys
sys.path.insert(0,'scripts/build/phase2')
from verify_stage import inspect_stage
from package_copyright import write_copyright
log=Path('/var/log/toddy')
failed=json.loads((log/'build/b01-qtbase-probe-install.failed.json').read_text())
assert failed['recipe_exit']==1 and failed['postcheck_exit'] is None and failed['changed_paths']==0
assert 'requires retained upstream/project copyright notices' in (log/'build/b01-qtbase-probe-install.log').read_text()
assert not (log/'packages/qtbase_6.11.2-1+toddy1_amd64.json').exists()
assert not Path('/var/cache/toddy/packages/qtbase_6.11.2-1+toddy1_amd64.deb').exists()
stage=Path('/mnt/lfs/sources/stage/phase2-qtbase-probe')
original=json.loads((log/'phase2/qtbase-probe-stage.json').read_text())['entries']
current=inspect_stage(stage)['entries']
assert all(current.get(k)==v for k,v in original.items())
assert all(k in original or k in {'usr/share/doc','usr/share/doc/qtbase'} or k == 'usr/share/doc/qtbase/source-notices' or k.startswith('usr/share/doc/qtbase/source-notices/') for k in current)
write_copyright(stage,'qtbase',['qtbase-everywhere-src-6.11.2.tar.xz'])
VERIFY
python3 scripts/build/stage_package.py qtbase 6.11.2-1+toddy1 \
    "$LFS/sources/stage/phase2-qtbase-probe" \
    --source qtbase-everywhere-src-6.11.2.tar.xz \
    --recipe scripts/build/phase2/qtbase-probe-package.sh \
    --depends 'glibc (>= 2.44-1), gcc (>= 16.2.0-1), dbus (>= 1.16.2-1), openssl (>= 4.0.3-1), zlib (>= 1.3.2-1), zstd (>= 1.5.7-1), glib (>= 2.88.3-1), systemd (>= 261.2-1)' --install
