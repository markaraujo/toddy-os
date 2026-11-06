#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.67-8.73; Patch overlay is ADR-0013.
set -euo pipefail
cd /sources/libpipeline-1.5.8
test ! -e /sources/stage/libpipeline
mkdir -p /sources/evidence/h07-libpipeline
./configure --prefix=/usr
make
# LFS 13.1 8.69: suite needs Check, absent from LFS. Native pipeline probe follows.
make DESTDIR=/sources/stage/libpipeline install
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-libpipeline/test-reports.tar.gz
mkdir -p /sources/stage/libpipeline/usr/share/doc/libpipeline
cp COPYING /sources/stage/libpipeline/usr/share/doc/libpipeline/copyright
