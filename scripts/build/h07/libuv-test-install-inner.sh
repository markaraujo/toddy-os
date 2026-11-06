#!/bin/bash
set -euo pipefail
cd /sources/libuv-v1.52.1
test ! -e /sources/stage/libuv
mkdir -p /sources/evidence/h07-libuv/initial-root-group
cp /sources/evidence/h07-libuv/check.log /sources/evidence/h07-libuv/initial-root-group/
chown -R tester:tester .
su tester -c 'make check' 2>&1 | tee /sources/evidence/h07-libuv/check.log
make DESTDIR=/sources/stage/libuv install
mkdir -p /sources/stage/libuv/usr/share/doc/libuv
cat LICENSE LICENSE-extra LICENSE-docs > /sources/stage/libuv/usr/share/doc/libuv/copyright
