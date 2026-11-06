#!/bin/bash
# Supplemental source additions frozen in ADR-0024.
set -euo pipefail
cd /sources/libmd-1.3.0
test ! -e /sources/stage/libmd
mkdir -p /sources/evidence/h07-libmd
./configure --prefix=/usr --disable-static
make
make check 2>&1 | tee /sources/evidence/h07-libmd/check.log
make DESTDIR=/sources/stage/libmd install
mkdir -p /sources/stage/libmd/usr/share/doc/libmd
cat COPYING > /sources/stage/libmd/usr/share/doc/libmd/copyright
