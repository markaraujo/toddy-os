#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: gettext; stage and preserve full tests.
set -euo pipefail
cd /sources/gettext-1.0
test ! -e /sources/stage/gettext
./configure --prefix=/usr --disable-static --docdir=/usr/share/doc/gettext-1.0
make
mkdir -p /sources/evidence/h07-gettext
make check 2>&1 | tee /sources/evidence/h07-gettext/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-gettext/test-reports.tar.gz
make DESTDIR=/sources/stage/gettext install
chmod -v 0755 /sources/stage/gettext/usr/lib/preloadable_libintl.so
mkdir -p /sources/stage/gettext/usr/share/doc/gettext
cp COPYING /sources/stage/gettext/usr/share/doc/gettext/copyright
