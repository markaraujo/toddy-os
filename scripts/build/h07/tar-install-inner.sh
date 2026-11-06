#!/bin/bash
set -euo pipefail
cd /sources/tar-1.35
test ! -e /sources/stage/tar
cp tests/testsuite.dir/233/testsuite.log /sources/evidence/h07-tar/capability-test.log
printf '2\n' > /sources/evidence/h07-tar/check.exit
python3 /sources/toddy-evaluate-tar.py /sources/evidence/h07-tar
make DESTDIR=/sources/stage/tar install
make -C doc DESTDIR=/sources/stage/tar install-html docdir=/usr/share/doc/tar-1.35
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-tar/test-reports.tar.gz
mkdir -p /sources/stage/tar/usr/share/doc/tar
cp COPYING /sources/stage/tar/usr/share/doc/tar/copyright
