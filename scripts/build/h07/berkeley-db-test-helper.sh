#!/bin/bash
# Restore only the missing native test process; never install it in the package.
source /opt/toddy-build/scripts/build/h06/common.sh
python3 - <<'PY'
from pathlib import Path
import hashlib
source=Path('/opt/toddy-build/scripts/build/h07/db_repsite.c')
expected='827f84ea724f12d6c91c5b215026e0e771a896423b67654690bd85ffaf08735c'
payload=source.read_bytes()
if hashlib.sha256(payload).hexdigest()!=expected:
    raise SystemExit('Native test adapter differs from the fully exercised source')
build=Path('/mnt/lfs/sources/db-5.3.28/build-test')
if build.resolve()!=build or not build.is_dir():
    raise SystemExit('Redirected or absent native test build')
target=build/'db_repsite.c'
if target.is_symlink():raise SystemExit('Redirected test adapter source')
if target.exists() and target.read_bytes()!=payload:
    raise SystemExit('Preserve unexpected existing test adapter for diagnosis')
target.write_bytes(payload)
target.chmod(0o644)
print('Verified native test-only adapter:',expected)
PY
chroot_run <<'INNER'
set -euo pipefail
cd /sources/db-5.3.28/build-test
test ! -L db_repsite
test ! -e db_repsite.new
su tester -c "cc -O2 -std=gnu17 -Wall -Wextra -Werror -I. db_repsite.c -L.libs '-Wl,-rpath,\$ORIGIN/.libs' -l:libdb-5.3.so -pthread -o db_repsite.new"
test -x db_repsite.new
mv -T db_repsite.new db_repsite
sha256sum db_repsite.c db_repsite
INNER
