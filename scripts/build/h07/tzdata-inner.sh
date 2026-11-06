#!/bin/bash
# LFS 13.1-systemd 8.5 time-zone compilation, staged as its own native package.
set -euo pipefail
cd /sources/tzdata-2026c
stage=/sources/stage/tzdata
test ! -e "$stage"
zoneinfo=$stage/usr/share/zoneinfo
mkdir -p "$zoneinfo"/{posix,right} "$stage/usr/share/doc/tzdata"
for tz in etcetera southamerica northamerica europe africa antarctica asia australasia backward; do
    zic -L /dev/null -d "$zoneinfo" "$tz"
    zic -L /dev/null -d "$zoneinfo/posix" "$tz"
    zic -L leapseconds -d "$zoneinfo/right" "$tz"
done
cp -v zone.tab zone1970.tab iso3166.tab "$zoneinfo"
zic -d "$zoneinfo" -p America/New_York
cp LICENSE "$stage/usr/share/doc/tzdata/copyright"
