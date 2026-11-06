#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.52-8.54, explicit Python security overlay.
set -euo pipefail
cd /sources/mpdecimal-4.0.1
test ! -e /sources/stage/mpdecimal
./configure --prefix=/usr --disable-static --docdir=/usr/share/doc/mpdecimal-4.0.1
make
mkdir -p /sources/evidence/h07-mpdecimal
make check_local 2>&1 | tee /sources/evidence/h07-mpdecimal/check.log
make DESTDIR=/sources/stage/mpdecimal install
mkdir -p /sources/stage/mpdecimal/usr/share/doc/mpdecimal
cp COPYRIGHT.txt /sources/stage/mpdecimal/usr/share/doc/mpdecimal/copyright
