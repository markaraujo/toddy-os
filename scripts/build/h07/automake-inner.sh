#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; security overlays and generic ISA explicit.
set -euo pipefail
cd /sources/automake-1.18.1
test ! -e /sources/stage/automake
./configure --prefix=/usr --docdir=/usr/share/doc/automake-1.18.1
make
mkdir -p /sources/evidence/h07-automake
make -j8 check 2>&1 | tee /sources/evidence/h07-automake/check.log
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-automake/test-reports.tar.gz
make DESTDIR=/sources/stage/automake install
mkdir -p /sources/stage/automake/usr/share/doc/automake
cat COPYING > /sources/stage/automake/usr/share/doc/automake/copyright
