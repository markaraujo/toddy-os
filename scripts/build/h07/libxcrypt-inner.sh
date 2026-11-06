#!/bin/bash
# Frozen LFS 13.1-systemd 8.29. No legacy binary-only ABI is required.
set -euo pipefail
cd /sources/libxcrypt-4.5.2
test ! -e /sources/stage/libxcrypt
sed -i '/strchr/s/const//' lib/crypt-{sm3,gost}-yescrypt.c
./configure --prefix=/usr --enable-hashes=strong,glibc --enable-obsolete-api=no \
 --disable-static --disable-failure-tokens
make
mkdir -p /sources/evidence/h07-libxcrypt
make check 2>&1 | tee /sources/evidence/h07-libxcrypt/check.log
find . -type f \( -name '*.log' -o -name '*.trs' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-libxcrypt/test-reports.tar.gz
make DESTDIR=/sources/stage/libxcrypt install
mkdir -p /sources/stage/libxcrypt/usr/share/doc/libxcrypt
cp COPYING.LIB /sources/stage/libxcrypt/usr/share/doc/libxcrypt/copyright
