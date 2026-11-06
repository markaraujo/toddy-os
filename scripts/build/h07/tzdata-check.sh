#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' tzdata) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
test -f /usr/share/zoneinfo/America/Sao_Paulo
test -f /usr/share/zoneinfo/right/UTC
TZ=America/Sao_Paulo date -d '2026-11-05 12:00:00 UTC' '+%H:%M %z' | grep -Fx '09:00 -0300'
INNER
