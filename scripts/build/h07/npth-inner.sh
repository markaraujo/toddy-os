#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with authenticated additions in ADR-0026.
set -euo pipefail
cd /sources/npth-1.8
test ! -e /sources/stage/npth
mkdir -p /sources/evidence/h07-npth
./configure --prefix=/usr --sysconfdir=/etc --disable-static
make
make check 2>&1 | tee /sources/evidence/h07-npth/check.log
make DESTDIR=/sources/stage/npth install
mkdir -p /sources/stage/npth/usr/share/doc/npth
cat COPYING* > /sources/stage/npth/usr/share/doc/npth/copyright
if [[ -d LICENSES ]]; then cp -a LICENSES /sources/stage/npth/usr/share/doc/npth/; fi
