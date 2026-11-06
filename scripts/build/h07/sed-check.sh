#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' sed) == 'install ok installed' ]]
check_native /usr/bin/sed 4.10
chroot_run <<'INNER'
set -euo pipefail
printf 'native\n' | sed 's/native/SED_OK/' | grep -Fx SED_OK
INNER
