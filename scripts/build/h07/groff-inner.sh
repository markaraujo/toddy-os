#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.60-8.66; build only in guarded target.
set -euo pipefail
cd /sources/groff-1.24.1
test ! -e /sources/stage/groff
mkdir -p /sources/evidence/h07-groff
PAGE=A4 ./configure --prefix=/usr
make -j1
# The neqn wrapper invokes the newly built eqn through PATH.
PATH="$PWD:$PATH" make check 2>&1 | tee /sources/evidence/h07-groff/check.log
make DESTDIR=/sources/stage/groff install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-groff/test-reports.tar.gz
mkdir -p /sources/stage/groff/usr/share/doc/groff
cat COPYING > /sources/stage/groff/usr/share/doc/groff/copyright
