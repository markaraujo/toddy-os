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
python3 /opt/toddy-build/scripts/build/apply_db_test_fixture.py
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-inner.sh
bash /opt/toddy-build/scripts/build/h07/berkeley-db-test-helper.sh
python3 /opt/toddy-build/scripts/build/verify_db_tcl_tests.py
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-fixture-check-inner.sh
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-finish-inner.sh
bash /opt/toddy-build/scripts/build/h07/berkeley-db-package.sh "$0"
