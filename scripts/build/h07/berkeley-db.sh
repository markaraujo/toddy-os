#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" db5.3_5.3.28+dfsg2.orig.tar.xz
python3 "$SOURCE_TOOL" --verify-only db5.3_5.3.28+dfsg2-12.debian.tar.xz
python3 - <<'PY'
from pathlib import Path
import tarfile
root=Path('/mnt/lfs/sources/db-5.3.28');assert not (root/'debian').exists()
with tarfile.open('/mnt/lfs/sources/db5.3_5.3.28+dfsg2-12.debian.tar.xz') as archive:
 members=[m for m in archive.getmembers() if m.name in ['debian','debian/patches','debian/copyright','debian/changelog'] or m.name.startswith('debian/patches/')]
 assert all(m.isfile() or m.isdir() for m in members)
 archive.extractall(root,members=members,filter='data')
PY
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-inner.sh
python3 /opt/toddy-build/scripts/build/stage_package.py berkeley-db 5.3.28+dfsg2-12.1 \
 "$LFS/sources/stage/berkeley-db" --depends 'glibc (>= 2.44-1)' \
 --source db5.3_5.3.28+dfsg2.orig.tar.xz --source db5.3_5.3.28+dfsg2-12.debian.tar.xz \
 --recipe /opt/toddy-build/scripts/build/h07/berkeley-db.sh --install
