#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' bc) == 'install ok installed' ]]
check_native /usr/bin/bc 7.0.3
chroot_run <<'INNER'
set -euo pipefail
printf '6*7\n' | bc | grep -Fx '42'
INNER
