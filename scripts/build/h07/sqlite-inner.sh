#!/bin/bash
# Frozen LFS 13.1-systemd sections 8.52-8.54, explicit Python security overlay.
set -euo pipefail
cd /sources/sqlite-autoconf-3530400
test ! -e /sources/stage/sqlite
./configure --prefix=/usr --disable-static --enable-fts{4,5} \
 CPPFLAGS="-D SQLITE_ENABLE_COLUMN_METADATA=1 -D SQLITE_ENABLE_UNLOCK_NOTIFY=1 -D SQLITE_ENABLE_DBSTAT_VTAB=1 -D SQLITE_SECURE_DELETE=1"
make LDFLAGS.rpath=""
# Frozen LFS 13.1 section 8.52: this autoconf distribution has no test suite.
make DESTDIR=/sources/stage/sqlite install
mkdir -p /sources/stage/sqlite/usr/share/doc/sqlite
head -n 11 sqlite3.h > /sources/stage/sqlite/usr/share/doc/sqlite/copyright
