#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: mpc; retained full native suite.
set -euo pipefail
cd /sources/mpc-1.4.1
test ! -e /sources/stage/mpc
./configure --prefix=/usr --disable-static  \
 --docdir=/usr/share/doc/mpc-1.4.1
make
make html
mkdir -p /sources/evidence/h07-mpc
make check 2>&1 | tee /sources/evidence/h07-mpc/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-mpc/test-reports.tar.gz
make DESTDIR=/sources/stage/mpc install
make DESTDIR=/sources/stage/mpc install-html
mkdir -p /sources/stage/mpc/usr/share/doc/mpc
cat COPYING* > /sources/stage/mpc/usr/share/doc/mpc/copyright
