#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' zstd) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
zstd --version | grep '1.5.7'
printf 'Native zstd roundtrip\n' | zstd -c | zstd -dc | grep -Fx 'Native zstd roundtrip'
INNER
