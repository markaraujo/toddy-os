#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' bzip2) == 'install ok installed' ]]
chroot_run <<'INNER'
set -euo pipefail
printf 'Native bzip2 roundtrip\n' | bzip2 -c | bzip2 -dc | grep -Fx 'Native bzip2 roundtrip'
ldd /usr/bin/bzip2 | grep libbz2
INNER
