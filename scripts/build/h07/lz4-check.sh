#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' lz4) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
lz4 --version | grep '1.10.0'
printf 'Native lz4 roundtrip\n' | lz4 -c | lz4 -dc | grep -Fx 'Native lz4 roundtrip'
INNER
