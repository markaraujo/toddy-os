#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.60-8.66; build only in guarded target.
set -euo pipefail
cd /sources/diffutils-3.12
test ! -e /sources/stage/diffutils
mkdir -p /sources/evidence/h07-diffutils
./configure --prefix=/usr
make
make check 2>&1 | tee /sources/evidence/h07-diffutils/check.log
make DESTDIR=/sources/stage/diffutils install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-diffutils/test-reports.tar.gz
mkdir -p /sources/stage/diffutils/usr/share/doc/diffutils
cat COPYING > /sources/stage/diffutils/usr/share/doc/diffutils/copyright
