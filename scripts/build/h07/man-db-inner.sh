#!/bin/bash
# Frozen LFS 13.1-systemd chapter 8; guarded disposable target only.
set -euo pipefail
cd /sources/man-db-2.13.1
test ! -e /sources/stage/man-db
mkdir -p /sources/evidence/h07-man-db
./configure --prefix=/usr --docdir=/usr/share/doc/man-db-2.13.1 \
 --sysconfdir=/etc --disable-setuid --enable-cache-owner=bin \
 --with-browser=/usr/bin/lynx --with-vgrind=/usr/bin/vgrind --with-grap=/usr/bin/grap
make
make check 2>&1 | tee /sources/evidence/h07-man-db/check.log
make DESTDIR=/sources/stage/man-db install

mkdir -p /sources/stage/man-db/usr/share/doc/man-db
cat COPYING > /sources/stage/man-db/usr/share/doc/man-db/copyright
