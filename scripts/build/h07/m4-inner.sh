#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: m4, staged native installation.
set -euo pipefail
cd /sources/m4-1.4.21
test ! -e /sources/stage/m4
./configure --prefix=/usr

make

make check

make DESTDIR=/sources/stage/m4 install
mkdir -p /sources/stage/m4/usr/share/doc/m4
cp COPYING /sources/stage/m4/usr/share/doc/m4/copyright
