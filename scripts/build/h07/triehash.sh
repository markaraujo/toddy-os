#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
cd "$LFS/sources"
python3 "$SOURCE_TOOL" triehash_0.3.orig.tar.gz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/triehash-0.3
test ! -e /sources/stage/triehash
mkdir -p /sources/evidence/h07-triehash
chown -R tester:tester .
su tester -c './tests/run-tests.sh' 2>&1 | tee /sources/evidence/h07-triehash/check.log
install -Dm755 triehash.pl /sources/stage/triehash/usr/bin/triehash
install -Dm644 LICENSE.md /sources/stage/triehash/usr/share/doc/triehash/copyright
INNER
python3 /opt/toddy-build/scripts/build/stage_package.py triehash 0.3-1 \
 "$LFS/sources/stage/triehash" --architecture all --depends perl \
 --source triehash_0.3.orig.tar.gz --recipe /opt/toddy-build/scripts/build/h07/triehash.sh --install
