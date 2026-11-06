#!/bin/bash
# Frozen BLFS 13.1-systemd Time 1.10; required by XXHash's full tool tests.
set -euo pipefail
cd /sources/time-1.10
test ! -e /sources/stage/time
mkdir -p /sources/evidence/h07-time
./configure --prefix=/usr
make
make check 2>&1 | tee /sources/evidence/h07-time/check.log
make DESTDIR=/sources/stage/time install
mkdir -p /sources/stage/time/usr/share/doc/time
cat COPYING > /sources/stage/time/usr/share/doc/time/copyright
