#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; security overlays and generic ISA explicit.
set -euo pipefail
cd /sources/libffi-3.8.0
test ! -e /sources/stage/libffi
./configure --prefix=/usr --disable-static --without-gcc-arch
make
mkdir -p /sources/evidence/h07-libffi
make check 2>&1 | tee /sources/evidence/h07-libffi/check.log
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-libffi/test-reports.tar.gz
make DESTDIR=/sources/stage/libffi install
mkdir -p /sources/stage/libffi/usr/share/doc/libffi
cat LICENSE LICENSE-BUILDTOOLS > /sources/stage/libffi/usr/share/doc/libffi/copyright
