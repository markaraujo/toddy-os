#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only libuv-v1.52.1.tar.gz
python3 - <<'CHECK'
from pathlib import Path
import json
r=json.loads(Path('/var/log/toddy/build/h07-libuv.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
assert not Path('/mnt/lfs/sources/stage/libuv').exists()
log=Path('/mnt/lfs/sources/evidence/h07-libuv/check.log').read_text()
failures=[l for l in log.splitlines() if l.startswith('not ok ')]
assert failures==['not ok 56 - fs_copyfile','not ok 57 - fs_copyfile_iouring']
assert log.count('stat_req.statbuf.st_gid == gid` (101 == 0)')==2
CHECK
chroot_run < /opt/toddy-build/scripts/build/h07/libuv-test-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py libuv 1.52.1-1 \
 "$LFS/sources/stage/libuv" --depends 'glibc (>= 2.44-1)' --source libuv-v1.52.1.tar.gz \
 --recipe /opt/toddy-build/scripts/build/h07/libuv-test-resume.sh --install
