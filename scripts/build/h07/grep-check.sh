#!/bin/bash
source /opt/toddy-build/scripts/build/h06/common.sh
[[ $(dpkg-query --admindir="$LFS/var/lib/dpkg" -W -f='${Status}' grep) == 'install ok installed' ]]
check_native /usr/bin/grep 3.12
chroot_run <<'INNER'
set -euo pipefail
printf 'value=42\n' | grep -P '^value=\d+$'
INNER
