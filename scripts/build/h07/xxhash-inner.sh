#!/bin/bash
# Supplemental source additions frozen in ADR-0024.
set -euo pipefail
cd /sources/xxHash-0.8.4
test ! -e /sources/stage/xxhash
mkdir -p /sources/evidence/h07-xxhash
make PREFIX=/usr
chown -R tester .
su tester -c 'make test' 2>&1 | tee /sources/evidence/h07-xxhash/check.log
make PREFIX=/usr DESTDIR=/sources/stage/xxhash install
mkdir -p /sources/stage/xxhash/usr/share/doc/xxhash
cat LICENSE > /sources/stage/xxhash/usr/share/doc/xxhash/copyright
