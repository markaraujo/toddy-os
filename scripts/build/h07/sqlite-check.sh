#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' sqlite) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
sqlite3 /tmp/toddy-sqlite.db <<'SQL'
BEGIN;
CREATE VIRTUAL TABLE entries USING fts5(value);
INSERT INTO entries VALUES ('native persistent');
COMMIT;
SQL
[[ $(sqlite3 /tmp/toddy-sqlite.db "SELECT value FROM entries WHERE entries MATCH 'native';") == 'native persistent' ]]
[[ $(sqlite3 /tmp/toddy-sqlite.db 'PRAGMA integrity_check;') == ok ]]
rm /tmp/toddy-sqlite.db
! readelf -d /usr/lib/libsqlite3.so | grep -E 'RPATH|RUNPATH'

INNER
