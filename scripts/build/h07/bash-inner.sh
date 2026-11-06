#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: bash; stage and preserve full tests.
set -euo pipefail
cd /sources/bash-5.3
test ! -e /sources/stage/bash
./configure --prefix=/usr --without-bash-malloc --with-installed-readline --docdir=/usr/share/doc/bash-5.3
make
mkdir -p /sources/evidence/h07-bash
chown -R tester .
LC_ALL=C.UTF-8 su -s /usr/bin/expect tester << 'EXPECT' 2>&1 | tee /sources/evidence/h07-bash/check.log
set timeout -1
spawn sh -c {exec 3>&- 4>&-; exec make -j1 tests}
expect eof
lassign [wait] _ _ _ value
exit $value
EXPECT
