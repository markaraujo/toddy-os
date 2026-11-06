#!/bin/bash
# Frozen LFS 13.1-systemd section 8.22; install only accepted build.
set -euo pipefail
cd /sources/binutils-2.47/build
test ! -e /sources/stage/binutils
make DESTDIR=/sources/stage/binutils tooldir=/usr install
rm -rfv /sources/stage/binutils/usr/lib/lib{bfd,ctf,ctf-nobfd,gprofng,opcodes,sframe}.a \
 /sources/stage/binutils/usr/share/doc/gprofng/
mkdir -p /sources/stage/binutils/usr/share/doc/binutils
cat ../COPYING ../COPYING.LIB ../COPYING3 ../COPYING3.LIB > \
 /sources/stage/binutils/usr/share/doc/binutils/copyright
