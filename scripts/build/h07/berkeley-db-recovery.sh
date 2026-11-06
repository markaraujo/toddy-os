#!/bin/bash
# Reuse only the hash-verified compiled test build; rerun the complete suite.
source /opt/toddy-build/scripts/build/h06/common.sh
for source in db5.3_5.3.28+dfsg2.orig.tar.xz db5.3_5.3.28+dfsg2-12.debian.tar.xz db-5.3.28-test142-environment-1.patch; do
 python3 "$SOURCE_TOOL" --verify-only "$source"
done
python3 /opt/toddy-build/scripts/build/db_test_build_checkpoint.py verify
python3 - <<'PY'
from pathlib import Path
from datetime import datetime,timezone
source=Path('/mnt/lfs/sources/db-5.3.28/build-test')
history=Path('/var/log/toddy/build/history')/('berkeley-db-before-corrected-suite-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));history.mkdir()
import shutil
for name in ['ALL.OUT','ALL.OUT.1','ALL.OUT.2']:
 if (source/name).is_file():shutil.copy2(source/name,history/name)
testdir=source/'TESTDIR'
if testdir.exists():
 assert testdir.is_dir() and not testdir.is_symlink()
 target=Path('/mnt/lfs/sources/recovery')/history.name;testdir.rename(target)
print('Preserved failed suite logs/state:',history)
PY
python3 /opt/toddy-build/scripts/build/apply_db_test_fixture.py
python3 /opt/toddy-build/scripts/build/verify_db_tcl_tests.py
chroot_run <<'INNER'
set -euo pipefail
cd /sources/db-5.3.28
su tester -c 'cd build-test && ./cutest' 2>&1 | tee /sources/evidence/h07-berkeley-db/cutest-recovery.log
INNER
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-fixture-check-inner.sh
chroot_run < /opt/toddy-build/scripts/build/h07/berkeley-db-finish-inner.sh
bash /opt/toddy-build/scripts/build/h07/berkeley-db-package.sh "$0"
