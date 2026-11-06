#!/bin/bash
# Frozen chapter 8 commands, reviewed DESTDIR adaptation; security deltas explicit.
set -euo pipefail
cd /sources/zstd-1.5.7
test ! -e /sources/stage/zstd
make prefix=/usr

make check

make prefix=/usr DESTDIR=/sources/stage/zstd install

rm -v /sources/stage/zstd/usr/lib/libzstd.a
mkdir -p /sources/stage/zstd/usr/share/doc/zstd
cat LICENSE COPYING > /sources/stage/zstd/usr/share/doc/zstd/copyright
