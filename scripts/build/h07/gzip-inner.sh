#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.60-8.66; build only in guarded target.
set -euo pipefail
cd /sources/gzip-1.14
test ! -e /sources/stage/gzip
mkdir -p /sources/evidence/h07-gzip
./configure --prefix=/usr
make
make check 2>&1 | tee /sources/evidence/h07-gzip/check.log
make DESTDIR=/sources/stage/gzip install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-gzip/test-reports.tar.gz
mkdir -p /sources/stage/gzip/usr/share/doc/gzip
cat COPYING > /sources/stage/gzip/usr/share/doc/gzip/copyright
