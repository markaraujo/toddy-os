#!/bin/bash
# Frozen BLFS 13.1-systemd recipe with ADR-0017/0021 pinned additions.
set -euo pipefail
cd /sources/libuv-v1.52.1
test ! -e /sources/stage/libuv
mkdir -p /sources/evidence/h07-libuv
sh autogen.sh
./configure --prefix=/usr --disable-static
make
chown -R tester:tester .
su tester -c 'make check' 2>&1 | tee /sources/evidence/h07-libuv/check.log
make DESTDIR=/sources/stage/libuv install
mkdir -p /sources/stage/libuv/usr/share/doc/libuv
cat LICENSE LICENSE-extra LICENSE-docs > /sources/stage/libuv/usr/share/doc/libuv/copyright
