#!/bin/bash
set -euo pipefail
cd /sources/xxHash-0.8.4
test ! -e /sources/stage/xxhash
mkdir -p /sources/evidence/h07-xxhash/initial-missing-time
cp /sources/evidence/h07-xxhash/check.log /sources/evidence/h07-xxhash/initial-missing-time/
test -x /usr/bin/time
chown -R tester:tester .
su tester -c 'make test' 2>&1 | tee /sources/evidence/h07-xxhash/check.log
make PREFIX=/usr DESTDIR=/sources/stage/xxhash install
mkdir -p /sources/stage/xxhash/usr/share/doc/xxhash
cat LICENSE > /sources/stage/xxhash/usr/share/doc/xxhash/copyright
