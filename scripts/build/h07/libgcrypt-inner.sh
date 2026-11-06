#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with authenticated additions in ADR-0026.
set -euo pipefail
cd /sources/libgcrypt-1.12.4
test ! -e /sources/stage/libgcrypt
mkdir -p /sources/evidence/h07-libgcrypt
./configure --prefix=/usr --sysconfdir=/etc --disable-static
make
make check 2>&1 | tee /sources/evidence/h07-libgcrypt/check.log
make DESTDIR=/sources/stage/libgcrypt install
mkdir -p /sources/stage/libgcrypt/usr/share/doc/libgcrypt
cat COPYING* > /sources/stage/libgcrypt/usr/share/doc/libgcrypt/copyright
if [[ -d LICENSES ]]; then cp -a LICENSES /sources/stage/libgcrypt/usr/share/doc/libgcrypt/; fi
