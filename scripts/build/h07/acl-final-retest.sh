#!/bin/bash
# Frozen LFS 13.1 section 8.27: full unchanged suite after final Coreutils.
source /opt/toddy-build/scripts/build/h06/common.sh
[[ -f /var/log/toddy/build/h07-coreutils.success.json || -f /var/log/toddy/build/h07-coreutils-recovery.success.json ]]
[[ $(chroot "$LFS" /usr/bin/dpkg-query -W -f='${Version}' coreutils) == 9.11-1* ]]
cd "$LFS/sources"
python3 "$SOURCE_TOOL" acl-2.4.0.tar.xz
chroot_run <<'INNER'
set -euo pipefail
cd /sources/acl-2.4.0
mkdir -p /sources/evidence/h07-acl-final
./configure --prefix=/usr --disable-static --docdir=/usr/share/doc/acl-2.4.0
make
make check 2>&1 | tee /sources/evidence/h07-acl-final/check.log
find . -type f \( -name '*.trs' -o -name '*.log' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-acl-final/test-reports.tar.gz
INNER
