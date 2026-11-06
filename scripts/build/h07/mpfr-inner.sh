#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: mpfr; retained full native suite.
set -euo pipefail
cd /sources/mpfr-4.2.2
test ! -e /sources/stage/mpfr
./configure --prefix=/usr --disable-static --enable-thread-safe \
 --docdir=/usr/share/doc/mpfr-4.2.2
make
make html
mkdir -p /sources/evidence/h07-mpfr
make check 2>&1 | tee /sources/evidence/h07-mpfr/check.log
count=$(find . -name '*.log' -exec grep -h '^PASS' {} + | wc -l)
[[ $count -ge 198 ]]
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-mpfr/test-reports.tar.gz
make DESTDIR=/sources/stage/mpfr install
make DESTDIR=/sources/stage/mpfr install-html
mkdir -p /sources/stage/mpfr/usr/share/doc/mpfr
cat COPYING* > /sources/stage/mpfr/usr/share/doc/mpfr/copyright
