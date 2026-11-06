#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; security overlays and generic ISA explicit.
set -euo pipefail
cd /sources/elfutils-0.195
test ! -e /sources/stage/libelf
./configure --prefix=/usr --disable-debuginfod --enable-libdebuginfod=dummy
make -C lib
make -C libelf
mkdir -p /sources/evidence/h07-libelf
make -k check 2>&1 | tee /sources/evidence/h07-libelf/check.log
find . -type f \( -name '*.log' -o -name '*.trs' -o -name '*.sum' \) -print0 | \
 tar --null -T - -czf /sources/evidence/h07-libelf/test-reports.tar.gz
make -C libelf DESTDIR=/sources/stage/libelf install
install -vDm644 config/libelf.pc /sources/stage/libelf/usr/lib/pkgconfig/libelf.pc
rm /sources/stage/libelf/usr/lib/libelf.a
mkdir -p /sources/stage/libelf/usr/share/doc/libelf
cat COPYING COPYING-LGPLV3 COPYING-GPLV2 > /sources/stage/libelf/usr/share/doc/libelf/copyright
