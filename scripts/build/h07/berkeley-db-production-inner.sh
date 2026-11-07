#!/bin/bash
set -euo pipefail
cd /sources/db-5.3.28
test ! -e /sources/stage/berkeley-db
cd build-production
CFLAGS='-O2 -std=gnu17' ../dist/configure --prefix=/usr --libdir=/usr/lib \
 --sysconfdir=/etc --localstatedir=/var --enable-static --disable-cxx \
 --disable-compat185 --disable-dbm --disable-java --disable-sql --disable-stl \
 --with-mutex=POSIX/pthreads/library --disable-tcl --disable-test
make
make DESTDIR=/sources/stage/berkeley-db install
# A test-process helper must never become a production payload.
test -z "$(find /sources/stage/berkeley-db -name 'db_repsite*' -print -quit)"
# Static objects are required by the maintained symbol-version generator only.
find /sources/stage/berkeley-db/usr/lib -maxdepth 1 -type f \( -name "*.a" -o -name "*.la" \) -delete
! grep -E '^#define CONFIG_TEST 1' db_config.h
cd ..
mkdir -p /sources/stage/berkeley-db/usr/share/doc/berkeley-db
cat LICENSE debian/copyright > /sources/stage/berkeley-db/usr/share/doc/berkeley-db/copyright
