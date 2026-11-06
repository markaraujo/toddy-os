#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: bison; stage and preserve full tests.
set -euo pipefail
cd /sources/bison-3.8.2
test ! -e /sources/stage/bison
./configure --prefix=/usr --docdir=/usr/share/doc/bison-3.8.2
make
mkdir -p /sources/evidence/h07-bison
make check 2>&1 | tee /sources/evidence/h07-bison/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-bison/test-reports.tar.gz
make DESTDIR=/sources/stage/bison install
mkdir -p /sources/stage/bison/usr/share/doc/bison
cp COPYING /sources/stage/bison/usr/share/doc/bison/copyright
