#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with ADR-0017/0021 pinned additions.
set -euo pipefail
cd /sources/libarchive-3.8.11
test ! -e /sources/stage/libarchive
mkdir -p /sources/evidence/h07-libarchive
./configure --prefix=/usr --disable-static
make
chown -R tester .
su tester -c 'make check' 2>&1 | tee /sources/evidence/h07-libarchive/check.log
make DESTDIR=/sources/stage/libarchive install
ln -s bsdunzip /sources/stage/libarchive/usr/bin/unzip
mkdir -p /sources/stage/libarchive/usr/share/doc/libarchive
cat COPYING > /sources/stage/libarchive/usr/share/doc/libarchive/copyright
