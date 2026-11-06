#!/bin/bash
# Frozen LFS 13.1-systemd 8.26, native ext4 extended-attribute tests.
set -euo pipefail
cd /sources/attr-2.6.0
test ! -e /sources/stage/attr
./configure --prefix=/usr --disable-static --sysconfdir=/etc \
 --docdir=/usr/share/doc/attr-2.6.0
make
mkdir -p /sources/evidence/h07-attr
make check 2>&1 | tee /sources/evidence/h07-attr/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-attr/test-reports.tar.gz
make DESTDIR=/sources/stage/attr install
mkdir -p /sources/stage/attr/usr/share/doc/attr
cat doc/COPYING doc/COPYING.LGPL > /sources/stage/attr/usr/share/doc/attr/copyright
