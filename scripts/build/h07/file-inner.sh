#!/bin/bash
# Frozen chapter 8 commands, reviewed DESTDIR adaptation; security deltas explicit.
set -euo pipefail
cd /sources/file-5.48
test ! -e /sources/stage/file
./configure --prefix=/usr

make

make check

make DESTDIR=/sources/stage/file install
mkdir -p /sources/stage/file/usr/share/doc/file
cat COPYING > /sources/stage/file/usr/share/doc/file/copyright
