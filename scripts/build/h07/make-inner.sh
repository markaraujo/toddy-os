#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.67-8.73; Patch overlay is ADR-0013.
set -euo pipefail
cd /sources/make-4.4.1
test ! -e /sources/stage/make
mkdir -p /sources/evidence/h07-make
./configure --prefix=/usr
make
chown -R tester .
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-make/check.log
make DESTDIR=/sources/stage/make install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-make/test-reports.tar.gz
mkdir -p /sources/stage/make/usr/share/doc/make
cp COPYING /sources/stage/make/usr/share/doc/make/copyright
