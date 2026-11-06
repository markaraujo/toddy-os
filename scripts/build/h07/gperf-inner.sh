#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; Expat security overlay per ADR-0013.
set -euo pipefail
cd /sources/gperf-3.3
test ! -e /sources/stage/gperf
./configure --prefix=/usr --docdir=/usr/share/doc/gperf-3.3
make
mkdir -p /sources/evidence/h07-gperf
chown -R tester .
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-gperf/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-gperf/test-reports.tar.gz
make DESTDIR=/sources/stage/gperf install

mkdir -p /sources/stage/gperf/usr/share/doc/gperf
cat COPYING > /sources/stage/gperf/usr/share/doc/gperf/copyright
