#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; Expat security overlay per ADR-0013.
set -euo pipefail
cd /sources/gdbm-1.26
test ! -e /sources/stage/gdbm
./configure --prefix=/usr --disable-static --enable-libgdbm-compat
make
mkdir -p /sources/evidence/h07-gdbm
chown -R tester .
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-gdbm/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-gdbm/test-reports.tar.gz
make DESTDIR=/sources/stage/gdbm install

mkdir -p /sources/stage/gdbm/usr/share/doc/gdbm
cat COPYING > /sources/stage/gdbm/usr/share/doc/gdbm/copyright
