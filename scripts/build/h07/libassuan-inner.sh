#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with authenticated additions in ADR-0026.
set -euo pipefail
cd /sources/libassuan-3.0.2
test ! -e /sources/stage/libassuan
mkdir -p /sources/evidence/h07-libassuan
./configure --prefix=/usr --sysconfdir=/etc --disable-static
make
make check 2>&1 | tee /sources/evidence/h07-libassuan/check.log
make DESTDIR=/sources/stage/libassuan install
mkdir -p /sources/stage/libassuan/usr/share/doc/libassuan
cat COPYING* > /sources/stage/libassuan/usr/share/doc/libassuan/copyright
if [[ -d LICENSES ]]; then cp -a LICENSES /sources/stage/libassuan/usr/share/doc/libassuan/; fi
