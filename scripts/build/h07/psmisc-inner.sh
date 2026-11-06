#!/bin/bash
# Frozen LFS 13.1-systemd 8.35.
set -euo pipefail
cd /sources/psmisc-23.7
test ! -e /sources/stage/psmisc
./configure --prefix=/usr
make
mkdir -p /sources/evidence/h07-psmisc
make check 2>&1 | tee /sources/evidence/h07-psmisc/check.log
make DESTDIR=/sources/stage/psmisc install
mkdir -p /sources/stage/psmisc/usr/share/doc/psmisc
cp COPYING /sources/stage/psmisc/usr/share/doc/psmisc/copyright
