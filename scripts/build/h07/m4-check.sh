#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' m4) == 'install ok installed' ]]
check_native /usr/bin/m4 1.4.21
chroot_run <<'INNER'
set -euo pipefail
printf 'eval(6*7)\n' | m4 | grep -Fx '42'
INNER
