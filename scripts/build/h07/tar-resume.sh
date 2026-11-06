#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
python3 "$SOURCE_TOOL" --verify-only tar-1.35.tar.xz
python3 "$SOURCE_TOOL" --verify-only tar-1.35-acl_fix-1.patch
python3 - <<'CHECK'
import json
from pathlib import Path
r=json.loads(Path('/var/log/toddy/build/h07-tar.failed.json').read_text())
assert r['recipe_exit']==2 and r['changed_paths']==0
assert not Path('/mnt/lfs/sources/stage/tar').exists()
CHECK
install -m644 /opt/toddy-build/scripts/build/h07/evaluate-tar.py "$LFS/sources/toddy-evaluate-tar.py"
chroot_run < /opt/toddy-build/scripts/build/h07/tar-install-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py tar 1.35-1 \
 "$LFS/sources/stage/tar" --depends 'glibc (>= 2.44-1), acl, attr' --source tar-1.35.tar.xz --source tar-1.35-acl_fix-1.patch \
 --recipe /opt/toddy-build/scripts/build/h07/tar-resume.sh --install
