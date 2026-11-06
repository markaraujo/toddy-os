#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.67-8.73; Patch overlay is ADR-0013.
set -euo pipefail
cd /sources/texinfo-7.3
test ! -e /sources/stage/texinfo
mkdir -p /sources/evidence/h07-texinfo
./configure --prefix=/usr
make
make check 2>&1 | tee /sources/evidence/h07-texinfo/check.log
make DESTDIR=/sources/stage/texinfo install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-texinfo/test-reports.tar.gz
mkdir -p /sources/stage/texinfo/usr/share/doc/texinfo
cp COPYING /sources/stage/texinfo/usr/share/doc/texinfo/copyright
