#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' xxhash) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf '' | xxhsum -H64 | grep -F ef46db3751d8e999
pkg-config --modversion libxxhash | grep -Fx 0.8.4
INNER
