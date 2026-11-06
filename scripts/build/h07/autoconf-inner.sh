#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; security overlays and generic ISA explicit.
set -euo pipefail
cd /sources/autoconf-2.73
test ! -e /sources/stage/autoconf
./configure --prefix=/usr
make
mkdir -p /sources/evidence/h07-autoconf
make check 2>&1 | tee /sources/evidence/h07-autoconf/check.log
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-autoconf/test-reports.tar.gz
make DESTDIR=/sources/stage/autoconf install
mkdir -p /sources/stage/autoconf/usr/share/doc/autoconf
cat COPYING COPYINGv3 COPYING.EXCEPTION > /sources/stage/autoconf/usr/share/doc/autoconf/copyright
