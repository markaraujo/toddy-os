#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with ADR-0017/0021 pinned additions.
set -euo pipefail
cd /sources/nghttp2-1.71.0
test ! -e /sources/stage/nghttp2
mkdir -p /sources/evidence/h07-nghttp2
./configure --prefix=/usr --disable-static --enable-lib-only --docdir=/usr/share/doc/nghttp2-1.71.0
make
make check 2>&1 | tee /sources/evidence/h07-nghttp2/check.log
make DESTDIR=/sources/stage/nghttp2 install
mkdir -p /sources/stage/nghttp2/usr/share/doc/nghttp2
cat COPYING > /sources/stage/nghttp2/usr/share/doc/nghttp2/copyright
