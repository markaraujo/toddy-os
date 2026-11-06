#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.67-8.73; Patch overlay is ADR-0013.
set -euo pipefail
cd /sources/kbd-2.10.0
test ! -e /sources/stage/kbd
mkdir -p /sources/evidence/h07-kbd
patch --batch --forward --fuzz=0 -Np1 -i ../kbd-2.10.0-backspace-1.patch
sed -i '/RESIZECONS_PROGS=/s/yes/no/' configure
sed -i 's/resizecons.8 //' docs/man/man8/Makefile.in
./configure --prefix=/usr --disable-vlock
make
make check 2>&1 | tee /sources/evidence/h07-kbd/check.log
make DESTDIR=/sources/stage/kbd install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-kbd/test-reports.tar.gz
mkdir -p /sources/stage/kbd/usr/share/doc/kbd
cp COPYING /sources/stage/kbd/usr/share/doc/kbd/copyright
