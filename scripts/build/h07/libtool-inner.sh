#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; Expat security overlay per ADR-0013.
set -euo pipefail
cd /sources/libtool-2.6.2
test ! -e /sources/stage/libtool
./configure --prefix=/usr
make
mkdir -p /sources/evidence/h07-libtool
chown -R tester .
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-libtool/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-libtool/test-reports.tar.gz
make DESTDIR=/sources/stage/libtool install
rm -f /sources/stage/libtool/usr/lib/libltdl.a
mkdir -p /sources/stage/libtool/usr/share/doc/libtool
cat COPYING libltdl/COPYING.LIB > /sources/stage/libtool/usr/share/doc/libtool/copyright
