#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8: bc, staged native installation.
set -euo pipefail
cd /sources/bc-7.0.3
test ! -e /sources/stage/bc
CC='gcc -std=c99' ./configure --prefix=/usr -G -O3 -r

make

make test

make DESTDIR=/sources/stage/bc install
mkdir -p /sources/stage/bc/usr/share/doc/bc
cp LICENSE.md /sources/stage/bc/usr/share/doc/bc/copyright
