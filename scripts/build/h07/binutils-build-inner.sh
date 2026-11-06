#!/bin/bash
# LFS 13.1-systemd 8.22, critical suite retained before any installation.
set -euo pipefail
cd /sources/binutils-2.47
mkdir build
cd build
../configure --prefix=/usr --sysconfdir=/etc --enable-ld=default \
 --enable-plugins --enable-shared --disable-werror --enable-64-bit-bfd \
 --enable-new-dtags --with-system-zlib --with-lib-path=/usr/lib \
 --enable-default-hash-style=gnu
make tooldir=/usr
mkdir -p /sources/evidence/h07-binutils
set +e
make -k check > /sources/evidence/h07-binutils/check.log 2>&1
result=$?
set -e
printf '%s\n' "$result" > /sources/evidence/h07-binutils/check.exit
find . -type f \( -name '*.sum' -o -name '*.log' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-binutils/test-reports.tar.gz
cat /sources/evidence/h07-binutils/check.log
exit "$result"
