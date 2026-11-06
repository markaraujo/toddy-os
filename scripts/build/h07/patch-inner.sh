#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.67-8.73; Patch overlay is ADR-0013.
set -euo pipefail
cd /sources/patch-2.8.1
test ! -e /sources/stage/patch
mkdir -p /sources/evidence/h07-patch
./configure --prefix=/usr
make
make check 2>&1 | tee /sources/evidence/h07-patch/check.log
make DESTDIR=/sources/stage/patch install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-patch/test-reports.tar.gz
mkdir -p /sources/stage/patch/usr/share/doc/patch
cp COPYING /sources/stage/patch/usr/share/doc/patch/copyright
