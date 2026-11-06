#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' gawk) == 'install ok installed' ]]
check_native /usr/bin/gawk 5.4.1
chroot_run <<'INNER'
set -euo pipefail
printf '6 7\n' | awk '{print $1*$2}' | grep -Fx 42
INNER
