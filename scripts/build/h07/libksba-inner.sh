#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with authenticated additions in ADR-0026.
set -euo pipefail
cd /sources/libksba-1.8.1
test ! -e /sources/stage/libksba
mkdir -p /sources/evidence/h07-libksba
./configure --prefix=/usr --sysconfdir=/etc --disable-static
make
make check 2>&1 | tee /sources/evidence/h07-libksba/check.log
make DESTDIR=/sources/stage/libksba install
mkdir -p /sources/stage/libksba/usr/share/doc/libksba
cat COPYING* > /sources/stage/libksba/usr/share/doc/libksba/copyright
if [[ -d LICENSES ]]; then cp -a LICENSES /sources/stage/libksba/usr/share/doc/libksba/; fi
