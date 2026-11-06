#!/bin/bash
# Frozen chapter 8 commands, reviewed DESTDIR adaptation; security deltas explicit.
set -euo pipefail
cd /sources/lz4-1.10.0
test ! -e /sources/stage/lz4
make BUILD_STATIC=no PREFIX=/usr

make -j1 check

make BUILD_STATIC=no PREFIX=/usr DESTDIR=/sources/stage/lz4 install
mkdir -p /sources/stage/lz4/usr/share/doc/lz4
cat LICENSE lib/LICENSE programs/COPYING > /sources/stage/lz4/usr/share/doc/lz4/copyright
