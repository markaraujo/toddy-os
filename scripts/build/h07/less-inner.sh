#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; Expat security overlay per ADR-0013.
set -euo pipefail
cd /sources/less-704
test ! -e /sources/stage/less
./configure --prefix=/usr --sysconfdir=/etc
make
mkdir -p /sources/evidence/h07-less
chown -R tester .
su tester -c "PATH=$PATH make check" 2>&1 | tee /sources/evidence/h07-less/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-less/test-reports.tar.gz
make DESTDIR=/sources/stage/less install

mkdir -p /sources/stage/less/usr/share/doc/less
cat COPYING LICENSE > /sources/stage/less/usr/share/doc/less/copyright
