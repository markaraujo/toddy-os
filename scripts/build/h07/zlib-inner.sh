#!/bin/bash
# Frozen LFS 13.1-systemd 8.6, native staged install.
set -euo pipefail
cd /sources/zlib-1.3.2
./configure --prefix=/usr
make
make check
stage=/sources/stage/zlib
test ! -e "$stage"
make DESTDIR="$stage" install
rm -fv "$stage/usr/lib/libz.a"
mkdir -p "$stage/usr/share/doc/zlib"
cp LICENSE "$stage/usr/share/doc/zlib/copyright"
