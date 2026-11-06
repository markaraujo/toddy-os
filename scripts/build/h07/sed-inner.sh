#!/bin/bash
# Frozen LFS 13.1-systemd 8.34; full suite as tester.
set -euo pipefail
cd /sources/sed-4.10
test ! -e /sources/stage/sed
./configure --prefix=/usr
make
make html
chown -R tester .
mkdir -p /sources/evidence/h07-sed
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-sed/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-sed/test-reports.tar.gz
make DESTDIR=/sources/stage/sed install
install -vDm644 doc/sed.html -t /sources/stage/sed/usr/share/doc/sed-4.10
mkdir -p /sources/stage/sed/usr/share/doc/sed
cp COPYING /sources/stage/sed/usr/share/doc/sed/copyright
