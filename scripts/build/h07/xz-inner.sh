#!/bin/bash
# LFS 13.1-systemd 8.8 flags, explicit 5.8.4 security maintenance in ADR-0010.
set -euo pipefail
cd /sources/xz-5.8.4
./configure --prefix=/usr --disable-static --docdir=/usr/share/doc/xz-5.8.4
make
make check
stage=/sources/stage/xz
test ! -e "$stage"
make DESTDIR="$stage" install
mkdir -p "$stage/usr/share/doc/xz"
cp COPYING* AUTHORS "$stage/usr/share/doc/xz/"
cat COPYING* > "$stage/usr/share/doc/xz/copyright"
