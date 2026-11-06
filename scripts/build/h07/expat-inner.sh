#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; Expat security overlay per ADR-0013.
set -euo pipefail
cd /sources/expat-2.10.0
test ! -e /sources/stage/expat
./configure --prefix=/usr --disable-static --docdir=/usr/share/doc/expat-2.10.0
make
mkdir -p /sources/evidence/h07-expat
chown -R tester .
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-expat/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-expat/test-reports.tar.gz
make DESTDIR=/sources/stage/expat install
install -v -m644 doc/*.html doc/*.css /sources/stage/expat/usr/share/doc/expat-2.10.0
mkdir -p /sources/stage/expat/usr/share/doc/expat
cat COPYING > /sources/stage/expat/usr/share/doc/expat/copyright
