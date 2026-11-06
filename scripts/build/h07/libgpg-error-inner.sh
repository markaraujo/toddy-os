#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with authenticated additions in ADR-0026.
set -euo pipefail
cd /sources/libgpg-error-1.61
test ! -e /sources/stage/libgpg-error
mkdir -p /sources/evidence/h07-libgpg-error
./configure --prefix=/usr --sysconfdir=/etc --disable-static
make
make check 2>&1 | tee /sources/evidence/h07-libgpg-error/check.log
make DESTDIR=/sources/stage/libgpg-error install
mkdir -p /sources/stage/libgpg-error/usr/share/doc/libgpg-error
cat COPYING* > /sources/stage/libgpg-error/usr/share/doc/libgpg-error/copyright
if [[ -d LICENSES ]]; then cp -a LICENSES /sources/stage/libgpg-error/usr/share/doc/libgpg-error/; fi
