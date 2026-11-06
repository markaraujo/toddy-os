#!/bin/bash
# Resume the already built GMP after a corrected result-format assertion.
set -euo pipefail
cd /sources/gmp-6.3.0
test ! -e /sources/stage/gmp
mkdir -p /sources/evidence/h07-gmp
make check 2>&1 | tee /sources/evidence/h07-gmp/check.log
count=$(find . -name '*.log' -exec grep -h '^PASS' {} + | wc -l)
[[ $count -ge 199 ]]
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-gmp/test-reports.tar.gz
make DESTDIR=/sources/stage/gmp install
make DESTDIR=/sources/stage/gmp install-html
mkdir -p /sources/stage/gmp/usr/share/doc/gmp
cat COPYING* > /sources/stage/gmp/usr/share/doc/gmp/copyright
